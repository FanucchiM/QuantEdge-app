package com.stockanalyzer.config;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Component
public class StockConfig {

    public static final List<Map<String, String>> US_STOCKS;
    public static final List<Map<String, String>> AR_STOCKS;
    public static final List<Map<String, String>> EU_STOCKS;
    public static final List<Map<String, String>> JP_STOCKS;

    static {
        List<Map<String, String>> usStocks = new ArrayList<>();
        List<Map<String, String>> arStocks = new ArrayList<>();
        List<Map<String, String>> euStocks = new ArrayList<>();
        List<Map<String, String>> jpStocks = new ArrayList<>();

        try {
            ObjectMapper mapper = new ObjectMapper();
            JsonNode root;

            // Load from classpath (resources/stock-config.json)
            InputStream is = StockConfig.class.getClassLoader().getResourceAsStream("stock-config.json");
            if (is == null) {
                throw new IOException("stock-config.json not found in classpath");
            }
            try (InputStream reader = is) {
                root = mapper.readTree(reader);
            }

            JsonNode stocks = root.path("stocks");

            for (JsonNode node : stocks.path("US")) {
                String symbol = node.asText();
                usStocks.add(Map.of("symbol", symbol, "market", "US"));
            }
            for (JsonNode node : stocks.path("AR")) {
                String symbol = node.asText();
                arStocks.add(Map.of("symbol", symbol, "market", "AR"));
            }
            for (JsonNode node : stocks.path("EU")) {
                String symbol = node.asText();
                euStocks.add(Map.of("symbol", symbol, "market", "EU"));
            }
            for (JsonNode node : stocks.path("JP")) {
                String symbol = node.asText();
                jpStocks.add(Map.of("symbol", symbol, "market", "JP"));
            }

        } catch (IOException e) {
            System.err.println("Warning: Could not load stock-config.json — " + e.getMessage());
        }

        US_STOCKS = List.copyOf(usStocks);
        AR_STOCKS = List.copyOf(arStocks);
        EU_STOCKS = List.copyOf(euStocks);
        JP_STOCKS = List.copyOf(jpStocks);
    }

    /**
     * Returns all stocks from all markets in a single list.
     * Useful for batch operations.
     */
    public static List<Map<String, String>> getAllStocks() {
        List<Map<String, String>> all = new ArrayList<>();
        all.addAll(US_STOCKS);
        all.addAll(AR_STOCKS);
        all.addAll(EU_STOCKS);
        all.addAll(JP_STOCKS);
        return List.copyOf(all);
    }

    /**
     * Returns stocks for a specific market.
     */
    public static List<Map<String, String>> getStocksByMarket(String market) {
        return switch (market.toUpperCase()) {
            case "US" -> US_STOCKS;
            case "AR" -> AR_STOCKS;
            case "EU" -> EU_STOCKS;
            case "JP" -> JP_STOCKS;
            default   -> List.of();
        };
    }
}
