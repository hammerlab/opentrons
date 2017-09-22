// robot selectors test
import {NAME, selectors, constants} from '../'

const makeState = (state) => ({[NAME]: state})

const {
  getSessionName,
  getConnectionStatus,
  getCommands,
  getRunProgress,
  getStartTime,
  getIsReadyToRun,
  getIsRunning,
  getIsPaused,
  getIsDone,
  getRunTime
} = selectors

describe('robot selectors', () => {
  test('getSessionName', () => {
    const state = makeState({sessionName: 'foobar.py'})
    expect(getSessionName(state)).toBe('foobar.py')
  })

  test('getConnectionStatus', () => {
    let state = {isConnected: false, connectRequest: {inProgress: false}}
    expect(getConnectionStatus(makeState(state))).toBe(constants.DISCONNECTED)

    state = {...state, connectRequest: {inProgress: true}}
    expect(getConnectionStatus(makeState(state))).toBe(constants.CONNECTING)

    state = {isConnected: true, connectRequest: {inProgress: false}}
    expect(getConnectionStatus(makeState(state))).toBe(constants.CONNECTED)
  })

  test('getIsReadyToRun', () => {
    const expectedStates = {
      loaded: true,
      running: false,
      error: false,
      finished: false,
      stopped: false,
      paused: false
    }

    Object.keys(expectedStates).forEach((sessionState) => {
      const state = makeState({sessionState})
      const expected = expectedStates[sessionState]
      expect(getIsReadyToRun(state)).toBe(expected)
    })
  })

  test('getIsRunning', () => {
    const expectedStates = {
      loaded: false,
      running: true,
      error: false,
      finished: false,
      stopped: false,
      paused: true
    }

    Object.keys(expectedStates).forEach((sessionState) => {
      const state = makeState({sessionState})
      const expected = expectedStates[sessionState]
      expect(getIsRunning(state)).toBe(expected)
    })
  })

  test('getIsPaused', () => {
    const expectedStates = {
      loaded: false,
      running: false,
      error: false,
      finished: false,
      stopped: false,
      paused: true
    }

    Object.keys(expectedStates).forEach((sessionState) => {
      const state = makeState({sessionState})
      const expected = expectedStates[sessionState]
      expect(getIsPaused(state)).toBe(expected)
    })
  })

  test('getIsDone', () => {
    const expectedStates = {
      loaded: false,
      running: false,
      error: true,
      finished: true,
      stopped: true,
      paused: false
    }

    Object.keys(expectedStates).forEach((sessionState) => {
      const state = makeState({sessionState})
      const expected = expectedStates[sessionState]
      expect(getIsDone(state)).toBe(expected)
    })
  })

  describe('command based', () => {
    const state = makeState({
      protocolCommands: [0, 4],
      protocolCommandsById: {
        0: {
          id: 0,
          description: 'foo',
          handledAt: '2017-08-30T12:00:00Z',
          children: [1]
        },
        1: {
          id: 1,
          description: 'bar',
          handledAt: '2017-08-30T12:00:01Z',
          children: [2, 3]
        },
        2: {
          id: 2,
          description: 'baz',
          handledAt: '2017-08-30T12:00:02Z',
          children: []
        },
        3: {
          id: 3,
          description: 'qux',
          handledAt: '',
          children: []
        },
        4: {
          id: 4,
          description: 'fizzbuzz',
          handledAt: '',
          children: []
        }
      }
    })

    test('getRunProgress', () => {
      expect(getRunProgress(state)).toEqual(50)
    })

    test('getStartTime', () => {
      expect(getStartTime(state)).toEqual('2017-08-30T12:00:00Z')
    })

    test('getStartTime without commands', () => {
      expect(getStartTime(makeState({protocolCommands: []})))
        .toEqual('')
    })

    test('getRunTime', () => {
      const testGetRunTime = (seconds, expected) => {
        const stateWithRunTime = {
          ...state,
          [NAME]: {
            ...state[NAME],
            runTime: Date.parse('2017-08-30T12:00:00.123Z') + (1000 * seconds)
          }
        }

        expect(getRunTime(stateWithRunTime)).toEqual(expected)
      }

      testGetRunTime(0, '00:00:00')
      testGetRunTime(1, '00:00:01')
      testGetRunTime(59, '00:00:59')
      testGetRunTime(60, '00:01:00')
      testGetRunTime(61, '00:01:01')
      testGetRunTime(3599, '00:59:59')
      testGetRunTime(3600, '01:00:00')
      testGetRunTime(3601, '01:00:01')
    })

    test('getRunTime without commands', () => {
      expect(getRunTime(makeState({protocolCommands: []})))
        .toEqual('00:00:00')
    })

    test('getCommands', () => {
      expect(getCommands(state)).toEqual([
        {
          id: 0,
          description: 'foo',
          handledAt: '2017-08-30T12:00:00Z',
          isCurrent: true,
          isLast: false,
          children: [
            {
              id: 1,
              description: 'bar',
              handledAt: '2017-08-30T12:00:01Z',
              isCurrent: true,
              isLast: false,
              children: [
                {
                  id: 2,
                  description: 'baz',
                  handledAt: '2017-08-30T12:00:02Z',
                  isCurrent: true,
                  isLast: true,
                  children: []
                },
                {
                  id: 3,
                  description: 'qux',
                  handledAt: '',
                  isCurrent: false,
                  isLast: false,
                  children: []
                }
              ]
            }
          ]
        },
        {
          id: 4,
          description: 'fizzbuzz',
          handledAt: '',
          isCurrent: false,
          isLast: false,
          children: []
        }
      ])
    })
  })
})
