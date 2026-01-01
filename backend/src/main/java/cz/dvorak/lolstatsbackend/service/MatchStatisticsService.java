package cz.dvorak.lolstatsbackend.service;

import cz.dvorak.lolstatsbackend.dto.RiotAccountDto;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestTemplate;
import org.springframework.stereotype.Service;

@Service
public class MatchStatisticsService {

    // -- README --
    // 1st https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/GLAVIAS/EUNE?api_key=xx
    // use puuid
    // 2nd https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/zrlja7hX5SKhn_83gSJSLjpV4iSQRwkfCLp_AAs_izsNgi4x6eYEe5_juETx2FhSzoCJCud9iAPS0Q/ids?api_key=xx
    // use 20 match ids to find details
    // 3rd https://europe.api.riotgames.com/lol/match/v5/matches/EUN1_3882220677?api_key=xx
    // find detail information about matches
    private final RestTemplate restTemplate;
    private final String apiKey;
    private final String baseUrl;

    public MatchStatisticsService(
            RestTemplate restTemplate,
            @Value("${riot.api-key}") String apiKey,
            @Value("${riot.base-url}") String baseUrl
    ) {
        this.restTemplate = restTemplate;
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
    }

    public RiotAccountDto getAccountByRiotId(String gameName, String tagLine) {

        String url = baseUrl +
                "/riot/account/v1/accounts/by-riot-id/" +
                gameName + "/" + tagLine;

        HttpHeaders headers = new HttpHeaders();
        headers.set("X-Riot-Token", apiKey);

        HttpEntity<Void> entity = new HttpEntity<>(headers);

        ResponseEntity<RiotAccountDto> response =
                restTemplate.exchange(
                        url,
                        HttpMethod.GET,
                        entity,
                        RiotAccountDto.class
                );

        return response.getBody();
    }
}