import React from 'react'
// import PropTypes from 'prop-types'
import styles from './UploadPanel.css'

export default function UploadPanel (props) {
  // Props needed: recent protocols, protocol file name (if uploaded), onUploadProtocol handler
  // TODO (ka) - toggle upload button with file name (if uploaded)
  const {onNavClick} = props
  return (
    <div className={styles.upload_panel}>
      <section className={styles.upload_menu} onClick={onNavClick}>
        <div className={styles.upload_icon}>
          <img src='../ui/img/plus.png' alt='upload' />
        </div>
      </section>
      <section className={styles.open_file}>
        <label className={styles.upload_btn} htmlFor='uploaded-file'>
          Open File
           <input className={styles.file} type='file' name='uploaded-file' id='uploaded-file' />
        </label>

      </section>

      <section className={styles.recent_files} />
    </div>
  )
}