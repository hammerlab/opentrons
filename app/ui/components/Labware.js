import React from 'react'
import PropTypes from 'prop-types'
import styles from 'Deck.css'

export default function Labware (props) {
  return (
    <div className={styles.slot} />
  )
}

Labware.propTypes = {
  isTiprack: PropTypes.bool.isRequired
}
