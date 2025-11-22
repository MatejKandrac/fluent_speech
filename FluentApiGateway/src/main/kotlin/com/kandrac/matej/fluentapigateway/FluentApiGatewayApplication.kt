package com.kandrac.matej.fluentapigateway

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication
import org.springframework.data.jpa.repository.config.EnableJpaAuditing

@SpringBootApplication
@EnableJpaAuditing
class FluentApiGatewayApplication

fun main(args: Array<String>) {
    runApplication<FluentApiGatewayApplication>(*args)
}
