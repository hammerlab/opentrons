// browser websocket client event-emitter/JSON wrapper for convenience
import EventEmitter from 'events'
import log from 'winston'

// TODO(mc): find out if buffering incomplete messages if needed
// ws frame size is pretty big, though, so it's probably unnecesary
function parseMessage (data) {
  let message

  try {
    message = JSON.parse(data)
  } catch (e) {
    log.warn('JSON parse error', e)
  }

  return message
}

export default class WebSocketClient extends EventEmitter {
  constructor (url) {
    super()
    this._ws = new WebSocket(url)
    this._ws.onopen = () => this.emit('open')
    this._ws.onmessage = (e) => this.emit('message', parseMessage(e.data))
    this._ws.onclose = (e) => this.emit('close', e.code, e.reason, e.wasClean)
    this._ws.onerror = (error) => this.emit('error', error)
  }

  get readyState () {
    return this._ws.readyState
  }

  get url () {
    return this._ws.url
  }

  close (code, reason) {
    this._ws.close(code, reason)
  }

  send (data) {
    this._ws.send(JSON.stringify(data))
  }
}
