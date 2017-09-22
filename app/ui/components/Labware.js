import React from 'react'
import PropTypes from 'prop-types'

export default function Labware (props) {
  const {container} = props
  return (
    <img src={`img/${container.type}.png`} alt={`${container.name}.png`} />
  )
}

Labware.propTypes = {
  isTiprack: PropTypes.bool.isRequired
}
