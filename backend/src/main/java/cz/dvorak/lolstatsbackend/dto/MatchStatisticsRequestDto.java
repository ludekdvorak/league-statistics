package cz.dvorak.lolstatsbackend.dto;

import java.util.Optional;

public class MatchStatisticsRequestDto {
    private String apiKey;
    private String summonerName;
    private Optional<String> hashTag;

}
