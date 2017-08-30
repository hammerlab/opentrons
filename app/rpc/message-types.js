// rcp message types
// IMPORTANT: these need to stay in sync with python server

// server to client
export const RESULT = 0
export const ACK = 1
export const NOTIFICATION = 2
export const CONTROL_MESSAGE = 3

// statuses
export const statuses = {
  SUCCESS: 'success',
  FAILURE: 'error'
}
