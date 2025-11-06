package com.kandrac.matej.fluentapigateway.config

import com.mongodb.MongoClientSettings
import com.mongodb.MongoCredential
import com.mongodb.ServerAddress
import com.mongodb.client.MongoClient
import com.mongodb.client.MongoClients
import com.mongodb.connection.ClusterSettings
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.data.mongodb.config.EnableMongoAuditing
import org.springframework.data.mongodb.core.MongoTemplate

@Configuration
@EnableMongoAuditing
class MongoConfiguration {
    @Value("\${spring.data.mongodb.host}")
    private lateinit var mongoHost: String

    @Value("\${spring.data.mongodb.port}")
    private var mongoPort: Int = 0

    @Value("\${spring.data.mongodb.database}")
    private lateinit var databaseName: String

    @Value("\${spring.data.mongodb.username}")
    private lateinit var mongoUsername: String

    @Value("\${spring.data.mongodb.password}")
    private lateinit var mongoPassword: String

    @Value("\${spring.data.mongodb.authentication-database}")
    private lateinit var authDatabase: String

    /**
     * This bean sets up the connection. Key property is credential, since it sets the
     * SCRAM-SHA-256 mechanism (which is MongoDB default from docker)
     */

    @Bean
    fun mongoClient(): MongoClient {
        val credential =
            MongoCredential.createScramSha256Credential(
                mongoUsername,
                authDatabase,
                mongoPassword.toCharArray(),
            )

        val serverAddress = ServerAddress(mongoHost, mongoPort)

        val clusterSettings =
            ClusterSettings
                .builder()
                .hosts(listOf(serverAddress))
                .build()

        val settings =
            MongoClientSettings
                .builder()
                .credential(credential)
                .applyToClusterSettings { it.applySettings(clusterSettings) }
                .build()

        return MongoClients.create(settings)
    }

    @Bean
    fun mongoTemplate(): MongoTemplate = MongoTemplate(mongoClient(), databaseName)

//    @Bean
//    fun auditorProvider(): AuditorAware<String> = SpringSecurityAuditor()
}
