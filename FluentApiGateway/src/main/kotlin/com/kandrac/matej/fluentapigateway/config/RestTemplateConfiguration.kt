package com.kandrac.matej.fluentapigateway.config

import org.apache.hc.client5.http.impl.classic.CloseableHttpClient
import org.apache.hc.client5.http.impl.classic.HttpClients
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory
import org.springframework.web.client.RestTemplate

@Configuration
class RestTemplateConfiguration {

    @Bean
    fun httpClient(): CloseableHttpClient = HttpClients.createDefault()

    @Bean
    fun restTemplate(httpClient: CloseableHttpClient): RestTemplate =
        RestTemplate(HttpComponentsClientHttpRequestFactory(httpClient))
}
