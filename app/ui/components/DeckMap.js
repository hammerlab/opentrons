import React from 'react'
import PropTypes from 'prop-types'
import styles from 'Deck.css'

export default function DeckMap (props) {
  return (
    <div className={styles.deck_wrapper}>

    </div>
  )
}

DeckMap.propTypes = {
  isEmpty: PropTypes.bool.isRequired
}

const deck = {
  1: {
    labware:null
  },
  2: {
      labware: {
      name: 'p200_tiprack',
      slot: 'B1',
      type: 'tiprack-200'
    }
  }
}
