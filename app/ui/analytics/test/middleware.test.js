// tests for the analytics middleware

import gtmConfig from '../gtm-config'
import analyticsMiddleware from '../middleware'

const createStore = () => {
  const store = {
    getState: jest.fn(() => ({})),
    dispatch: jest.fn()
  }

  const next = jest.fn()
  const invoke = (action) => analyticsMiddleware(store)(next)(action)

  return {store, next, invoke}
}

describe('analytics middleware', () => {
  it('ignores non-analytics actions', () => {
    const {next, invoke} = createStore()
    const action = {type: 'FOO'}

    invoke(action)
    expect(next).toHaveBeenCalledWith(action)
  })

  it('adds analytics events to the data layer', () => {
    const {next, invoke} = createStore()
    const action = {type: 'FOO', meta: {analytics: true}}

    invoke(action)
    expect(global[gtmConfig.DATA_LAYER_NAME]).toEqual([action])
    expect(next).toHaveBeenCalledWith(action)
  })
})
