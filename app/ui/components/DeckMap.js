import React from 'react'
// import PropTypes from 'prop-types'
import styles from './Deck.css'

export default function DeckMap (props) {
  const deck = {
    1: {
      labware: {
        name: 'p10_tiprack',
        slot: 'A1',
        type: 'tiprack-10ul'
      }
    },
    2: {
      labware: null
    },
    3: {
      labware: {
        name: 'tuberack_75',
        slot: 'C1',
        type: 'tube-rack-.75ml'
      }
    },
    4: {
      labware: null
    },
    5: {
      labware: null
    },
    6: {
      labware: null
    },
    7: {
      labware: null
    },
    8: {
      labware: null
    },
    9: {
      labware: null
    },
    10: {
      labware: null
    },
    11: {
      labware: null
    }
  }

  const makeDeck = () => {
    let deckMap = []
    for (let i in deck) {
      let slot = deck[i]
      let slotStyle = {
        gridArea: `slot-${i}`
      }
      slot.labware
      ? deckMap.push(<div id={i} style={slotStyle} className={styles.slot}>{slot.labware.name}</div>)
      : deckMap.push(<div id={i} style={slotStyle} className={styles.empty_slot}>{i}</div>)
    }
    return <div className={styles.deck}> {deckMap} </div>
  }

  let deckLayout = makeDeck()

  return (
    <div className={styles.deck_wrapper}>
      {deckLayout}
    </div>
  )
}

// DeckMap.propTypes = {
//   isEmpty: PropTypes.bool.isRequired
// }
