package cz.dvorak.lolstatsbackend.service;

import cz.dvorak.lolstatsbackend.dto.MatchStatisticsRequestDto;
import cz.dvorak.lolstatsbackend.dto.MatchStatisticsResponseDto;
import org.springframework.stereotype.Service;

@Service
public class MatchStatisticsService {
    public MatchStatisticsResponseDto getMatchStatistics(MatchStatisticsRequestDto request)
    {

        // https://eun1.api.riotgames.com/lol/platform/v3/champion-rotations?api_key=

        return null;
    }


}