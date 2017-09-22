import React from 'react'
import PropTypes from 'prop-types'
import styles from 'Deck.css'

export default function Labware (props) {
  const {container} = props
  return (
    <div className={styles.labware}>{container}</div>
  )
}

Labware.propTypes = {
  isTiprack: PropTypes.bool.isRequired
}
