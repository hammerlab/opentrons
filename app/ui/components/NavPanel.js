import React from 'react'
import classnames from 'classnames'
import Button from './Button'
import styles from './NavPanel.css'

const UploadPanel = props => {
  return (
    <div className={styles.nav_panel}>
      <section className={styles.choose_file}>
        <button className={styles.btn_new}>
          New File
        </button>
        <label className={styles.btn} htmlFor='uploaded-file'>
          Upload
           <input className={styles.file} type='file' name='uploaded-file' id='uploaded-file' />
        </label>
      </section>
    </div>
  )
}

const ConnectPanel = props => {
  const {isConnected, connectionStatus, onConnectClick} = props
  return (
    <div className={styles.nav_panel}>
      <section className={styles.connection_info}>
        <p>connect</p>
      </section>
      <section className={styles.connection_toggle}>
        <Button
          onClick={onConnectClick}
          disabled={isConnected}
          style={styles.btn}
        >
          Connect To Robot
        </Button>
      </section>
    </div>
  )
}

const panel = (props) => ({
  upload: <UploadPanel {...props} />,
  connect: <ConnectPanel {...props} />,
  setup: <div>setup</div>,
})

export default function NavPanel (props) {
  const {currentNavPanelTask} = props
  return <div >{panel(props)[currentNavPanelTask]}</div>
}
