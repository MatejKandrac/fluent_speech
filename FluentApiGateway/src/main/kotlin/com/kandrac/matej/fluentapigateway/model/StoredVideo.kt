package com.kandrac.matej.fluentapigateway.model

import org.springframework.data.annotation.CreatedDate
import org.springframework.data.annotation.Id
import org.springframework.data.mongodb.core.mapping.Document
import java.time.LocalDateTime

@Document(collection = "videos")
data class StoredVideo(
    @Id
    var id: String? = null,
    var filename: String? = null,
    @CreatedDate
    var createdAt: LocalDateTime = LocalDateTime.now(),
)
