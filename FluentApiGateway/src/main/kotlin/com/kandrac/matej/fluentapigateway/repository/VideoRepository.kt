package com.kandrac.matej.fluentapigateway.repository

import com.kandrac.matej.fluentapigateway.model.StoredVideo
import org.springframework.data.jpa.repository.JpaRepository

interface VideoRepository : JpaRepository<StoredVideo, Long>
