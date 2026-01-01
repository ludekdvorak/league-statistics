package cz.dvorak.lolstatsbackend.controller;

import cz.dvorak.lolstatsbackend.dto.MatchStatisticsRequestDto;
import cz.dvorak.lolstatsbackend.dto.MatchStatisticsResponseDto;
import cz.dvorak.lolstatsbackend.dto.RiotAccountDto;
import cz.dvorak.lolstatsbackend.service.MatchStatisticsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/matchStatistics")
public class MatchStatisticsController {

    @Autowired
    private MatchStatisticsService matchStatisticsService;


    @GetMapping
    public String test() {
      return "OK";
    }

    @GetMapping("/account")
    public RiotAccountDto getAccount(
            @RequestParam String gameName,
            @RequestParam String tagLine
    ) {
        return matchStatisticsService.getAccountByRiotId(gameName, tagLine);
    }
}