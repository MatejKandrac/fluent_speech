package com.kandrac.matej.fluentapigateway.repository

import com.kandrac.matej.fluentapigateway.model.StoredVideo
import org.springframework.data.mongodb.repository.MongoRepository

interface VideoRepository : MongoRepository<StoredVideo, String>
