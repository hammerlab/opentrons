import EventEmitter from 'events'
// TODO(mc, 2017-08-29): Disable winston and uuid because of worker-loader bug
// preventing webpackification of built-in node modules (os and crypto)
// import log from 'winston'
// import uuid from 'uuid/v4'

import WebSocketClient from './websocket-client'
import RemoteObject from './remote-object'
import {
  statuses,
  RESULT,
  ACK,
  NACK,
  NOTIFICATION,
  CONTROL_MESSAGE
} from './message-types'

// TODO(mc, 2017-08-29): see note about uuid above
let _uniqueId = 0
const uuid = () => `id-${_uniqueId++}`

// timeouts
const HANDSHAKE_TIMEOUT = 5000
const RECEIVE_CONTROL_TIMEOUT = 3000
const CLOSE_TIMEOUT = 1000
const CALL_ACK_TIMEOUT = 3000
const CALL_RESULT_TIMEOUT = 240000

// metadata constants
const REMOTE_TARGET_OBJECT = 0
const REMOTE_TYPE_OBJECT = 1

// event name utilities
const makeAckEventName = (token) => `ack:${token}`
const makeNackEventName = (token) => `nack:${token}`
const makeSuccessEventName = (token) => `success:${token}`
const makeFailureEventName = (token) => `failure:${token}`

// internal RPC over websocket client
// handles the socket itself and object context
class RpcContext extends EventEmitter {
  constructor (ws) {
    super()
    this._ws = ws
    this._resultTypes = new Map()
    this._typeObjectCache = new Map()
    this.remote = null
    // default max listeners is 10, we need more than that
    // keeping this at a finite number just in case we get a leak later
    this.setMaxListeners(100)

    ws.on('error', this._handleError.bind(this))
    ws.on('message', this._handleMessage.bind(this))
  }

  callRemote (id, name, args = []) {
    const self = this
    const token = uuid()
    const ackEvent = makeAckEventName(token)
    const nackEvent = makeNackEventName(token)
    const resultEvent = makeSuccessEventName(token)
    const failureEvent = makeFailureEventName(token)

    return new Promise((resolve, reject) => {
      let timeout

      const handleError = (reason) => {
        cleanup()
        reject(new Error(`Error in ${name}(${args.join(', ')}): ${reason}`))
      }

      const handleFailure = (result) => handleError(new Error(result))
      const handleNack = (reason) => handleError(`Received NACK with ${reason}`)

      const handleAck = () => {
        clearTimeout(timeout)
        timeout = setTimeout(
          () => handleError('Result timeout'),
          CALL_RESULT_TIMEOUT
        )

        this.once(resultEvent, handleSuccess)
        this.once(failureEvent, handleFailure)
      }

      const handleSuccess = (result) => {
        cleanup()

        RemoteObject(this, result)
          .then(resolve)
          .catch(reject)
      }

      function cleanup () {
        clearTimeout(timeout)
        self.removeAllListeners(ackEvent)
        self.removeAllListeners(nackEvent)
        self.removeAllListeners(resultEvent)
        self.removeAllListeners(failureEvent)
        self.removeListener('error', handleError)
      }

      this.once('error', handleError)
      this.once(ackEvent, handleAck)
      this.once(nackEvent, handleNack)
      this._send({$: {token}, id, name, args})
      timeout = setTimeout(
        () => handleError('ACK timeout'),
        CALL_ACK_TIMEOUT
      )
    })
  }

  resolveTypeValues (source) {
    const typeId = source.t

    if (!this._resultTypes.has(typeId)) {
      this._resultTypes.set(typeId, REMOTE_TYPE_OBJECT)
    }

    if (this._resultTypes.get(source.i) === REMOTE_TYPE_OBJECT) {
      return Promise.resolve({})
    }

    if (this._typeObjectCache.has(typeId)) {
      return Promise.resolve(this._typeObjectCache.get(typeId).v)
    }

    return this.callRemote(null, 'get_object_by_id', [typeId])
  }

  // close the websocket
  close () {
    const self = this

    return new Promise((resolve, reject) => {
      if (this._ws.readyState === this._ws.CLOSED) {
        return resolve()
      }

      let closeTimeout
      const finish = (error) => {
        cleanup()

        if (this._ws.readyState === this._ws.CLOSED) {
          return resolve()
        }

        reject(error || new Error('WebSocket is not closed'))
      }

      const handleClose = () => finish()

      function cleanup () {
        clearTimeout(closeTimeout)
        self._ws.removeListener('close', handleClose)
        self._ws.removeListener('error', finish)
      }

      this._ws.once('close', handleClose)
      this._ws.once('error', finish)
      this._ws.close()
      closeTimeout = setTimeout(
        () => finish(new Error('Timed out closing RPC client')),
        CLOSE_TIMEOUT
      )
    })
  }

  // cache required metadata from call results
  // filter type field from type object to avoid getting unecessary types
  _cacheCallResultMetadata (resultData) {
    if (!resultData || !resultData.i) {
      return
    }

    const id = resultData.i
    const typeId = resultData.t
    const value = resultData.v || {}

    // grab any type ids (including children) and set the flags
    this._resultTypes.set(typeId, REMOTE_TYPE_OBJECT)
    Object.keys(value)
      .map((key) => value[key])
      .filter((v) => v && v.t && v.v)
      .forEach((v) => this._cacheCallResultMetadata(v))

    if (!this._resultTypes.has(id)) {
      this._resultTypes.set(id, REMOTE_TARGET_OBJECT)
    } else if (this._resultTypes.get(id) === REMOTE_TYPE_OBJECT) {
      this._typeObjectCache.set(id, resultData)
    }
  }

  _send (message) {
    // log.debug('Sending: %j', message)
    this._ws.send(message)
  }

  _handleError (error) {
    this.emit('error', error)
  }

  // TODO(mc): split this method up
  _handleMessage (message) {
    // log.debug('Received message %j', message)

    const {$: meta, data} = message
    const type = meta.type

    switch (type) {
      case CONTROL_MESSAGE:
        const root = message.root
        const rootType = message.type
        // cache this instance to mark its type as a type object
        // then cache its type object
        this._cacheCallResultMetadata(root)
        this._cacheCallResultMetadata(rootType)

        RemoteObject(this, root)
          .then((remote) => {
            this.remote = remote
            this.emit('ready')
          })
          // .catch((e) => log.error('Error creating control remote', e))

        break

      case RESULT:
        if (meta.status === statuses.SUCCESS) {
          this._cacheCallResultMetadata(data)
          this.emit(makeSuccessEventName(meta.token), data)
        } else {
          this.emit(makeFailureEventName(meta.token), data)
        }

        break

      case ACK:
        this.emit(makeAckEventName(meta.token))
        break

      case NACK:
        this.emit(makeNackEventName(meta.token), message.reason)
        break

      case NOTIFICATION:
        this._cacheCallResultMetadata(data)

        RemoteObject(this, data)
          .then((remote) => this.emit('notification', remote))
          // .catch((e) => log.error('Error creating notification remote', e))

        break

      default:
        break
    }
  }
}

export default function Client (url) {
  const ws = new WebSocketClient(url)

  return new Promise((resolve, reject) => {
    let context
    let controlTimeout

    const handleReady = () => {
      cleanup()
      resolve(context)
    }

    const handleError = (error) => {
      cleanup()
      reject(error)
    }

    const handshakeTimeout = setTimeout(
      () => handleError(new Error('Handshake timeout')),
      HANDSHAKE_TIMEOUT
    )

    const handleOpen = () => {
      clearTimeout(handshakeTimeout)
      ws.removeListener('error', handleError)
      controlTimeout = setTimeout(
        () => handleError(new Error('Timeout getting control message')),
        RECEIVE_CONTROL_TIMEOUT
      )

      context = new RpcContext(ws)
        .once('ready', handleReady)
        .once('error', handleError)
    }

    function cleanup () {
      clearTimeout(handshakeTimeout)
      ws.removeListener('open', handleOpen)
      ws.removeListener('error', handleError)

      if (context) {
        clearTimeout(controlTimeout)
        context.removeListener('ready', handleReady)
        context.removeListener('error', handleError)
      }
    }

    ws.once('open', handleOpen)
    ws.once('error', handleError)
  })
}
