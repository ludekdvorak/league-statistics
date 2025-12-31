package cz.dvorak.lolstatsbackend.service;

import cz.dvorak.lolstatsbackend.dto.MatchStatisticsRequestDto;
import cz.dvorak.lolstatsbackend.dto.MatchStatisticsResponseDto;
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

    public MatchStatisticsResponseDto getMatchStatistics(MatchStatisticsRequestDto request)
    {


        return null;
    }


}