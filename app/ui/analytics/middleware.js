// analytics middleware
import gtmConfig from './gtm-config'

const {DATA_LAYER_NAME} = gtmConfig

export default function analyticsMiddleware () {
  const dataLayer = global[DATA_LAYER_NAME] = global[DATA_LAYER_NAME] || []

  return (next) => (action) => {
    const {meta} = action

    if (meta && meta.analytics) {
      dataLayer.push(action)
    }

    return next(action)
  }
}
