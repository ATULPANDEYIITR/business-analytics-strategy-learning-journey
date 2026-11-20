import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import java.util.UUID;
import java.util.stream.Collectors;

/*
 * MARKETING ANALYTICS
 *
 * Enterprise campaign measurement, attribution, customer acquisition,
 * conversion funnels, and reporting.
 *
 * Java 17, standard library only.
 */

public class MarketingAnalytics {

    enum Channel {
        SEARCH,
        SOCIAL,
        EMAIL,
        DISPLAY
    }

    enum CampaignStatus {
        PLANNED,
        ACTIVE,
        PAUSED,
        COMPLETED
    }

    enum EventType {
        IMPRESSION,
        CLICK,
        CONVERSION
    }

    enum AttributionModel {
        FIRST_TOUCH,
        LAST_TOUCH,
        LINEAR
    }

    static class MarketingException extends RuntimeException {
        MarketingException(String message) {
            super(message);
        }
    }

    static class ValidationException extends MarketingException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class NotFoundException extends MarketingException {
        NotFoundException(String message) {
            super(message);
        }
    }

    record Campaign(
        String id,
        String name,
        Channel channel,
        double budget,
        String objective
    ) {
        Campaign {
            if (id == null || id.isBlank() ||
                name == null || name.isBlank() ||
                objective == null || objective.isBlank()) {
                throw new ValidationException(
                    "Campaign identity and objective are required."
                );
            }

            if (!Double.isFinite(budget) || budget < 0) {
                throw new ValidationException("Invalid budget.");
            }

            Objects.requireNonNull(channel);
        }
    }

    record Customer(
        String id,
        double acquisitionCost,
        double lifetimeRevenue
    ) {
        Customer {
            if (id == null || id.isBlank()) {
                throw new ValidationException("Customer ID is required.");
            }

            if (!Double.isFinite(acquisitionCost) ||
                !Double.isFinite(lifetimeRevenue) ||
                acquisitionCost < 0 ||
                lifetimeRevenue < 0) {
                throw new ValidationException(
                    "Invalid customer financial values."
                );
            }
        }
    }

    record MarketingEvent(
        String id,
        String customerId,
        String campaignId,
        EventType type,
        Instant timestamp,
        double revenue
    ) {
        MarketingEvent {
            if (id == null || id.isBlank() ||
                customerId == null || customerId.isBlank() ||
                campaignId == null || campaignId.isBlank()) {
                throw new ValidationException("Incomplete event.");
            }

            Objects.requireNonNull(type);
            Objects.requireNonNull(timestamp);

            if (!Double.isFinite(revenue) || revenue < 0) {
                throw new ValidationException("Invalid event revenue.");
            }

            if (type != EventType.CONVERSION && revenue != 0) {
                throw new ValidationException(
                    "Revenue is valid only for conversion events."
                );
            }
        }
    }

    record Touchpoint(
        String campaignId,
        Instant timestamp
    ) {}

    record CampaignReport(
        String campaignId,
        long impressions,
        long clicks,
        long conversions,
        double spend,
        double revenue,
        double ctr,
        double conversionRate,
        double cpc,
        double cpa,
        double roas,
        double roi
    ) {}

    static final class CampaignLedger {
        private long impressions;
        private long clicks;
        private long conversions;
        private double spend;
        private double revenue;

        CampaignLedger() {}

        CampaignLedger(CampaignLedger source) {
            impressions = source.impressions;
            clicks = source.clicks;
            conversions = source.conversions;
            spend = source.spend;
            revenue = source.revenue;
        }

        void apply(MarketingEvent event) {
            switch (event.type()) {
                case IMPRESSION -> impressions++;

                case CLICK -> {
                    if (clicks >= impressions) {
                        throw new ValidationException(
                            "Click requires an impression."
                        );
                    }
                    clicks++;
                }

                case CONVERSION -> {
                    if (conversions >= clicks) {
                        throw new ValidationException(
                            "Conversion requires a click."
                        );
                    }

                    conversions++;
                    revenue += event.revenue();
                }
            }
        }

        void addSpend(double amount, double budget) {
            if (!Double.isFinite(amount) || amount < 0) {
                throw new ValidationException("Invalid spend.");
            }

            if (spend + amount > budget) {
                throw new ValidationException("Budget exceeded.");
            }

            spend += amount;
        }

        CampaignReport report(String campaignId) {
            return new CampaignReport(
                campaignId,
                impressions,
                clicks,
                conversions,
                spend,
                revenue,
                percent(clicks, impressions),
                percent(conversions, clicks),
                divide(spend, clicks),
                divide(spend, conversions),
                divide(revenue, spend),
                percent(revenue - spend, spend)
            );
        }
    }

    interface ReportService {
        CampaignReport generate(String campaignId);
    }

    static final class MarketingService implements ReportService {

        private final Map<String, Campaign> campaigns = new HashMap<>();
        private final Map<String, CampaignLedger> ledgers = new HashMap<>();
        private final Map<String, Customer> customers = new HashMap<>();

        private final Map<String, List<Touchpoint>> journeys = new HashMap<>();

        private final Set<String> processedEvents = new HashSet<>();

        private final Map<String, CampaignStatus> statuses = new HashMap<>();

        public void registerCampaign(Campaign campaign) {
            Objects.requireNonNull(campaign);

            if (campaigns.containsKey(campaign.id())) {
                throw new ValidationException("Duplicate campaign.");
            }

            campaigns.put(campaign.id(), campaign);
            ledgers.put(campaign.id(), new CampaignLedger());
            statuses.put(campaign.id(), CampaignStatus.PLANNED);
        }

        public void changeStatus(
            String campaignId,
            CampaignStatus next
        ) {
            CampaignStatus current = statuses.get(campaignId);

            if (current == null) {
                throw new NotFoundException("Campaign not found.");
            }

            boolean valid = switch (current) {
                case PLANNED ->
                    next == CampaignStatus.ACTIVE ||
                    next == CampaignStatus.COMPLETED;

                case ACTIVE ->
                    next == CampaignStatus.PAUSED ||
                    next == CampaignStatus.COMPLETED;

                case PAUSED ->
                    next == CampaignStatus.ACTIVE ||
                    next == CampaignStatus.COMPLETED;

                case COMPLETED -> false;
            };

            if (!valid) {
                throw new ValidationException(
                    "Invalid campaign state transition: " +
                    current + " -> " + next
                );
            }

            statuses.put(campaignId, next);
        }

        public void registerCustomer(Customer customer) {
            if (customers.putIfAbsent(
                customer.id(), customer
            ) != null) {
                throw new ValidationException("Duplicate customer.");
            }
        }

        public void recordEvent(MarketingEvent event) {
            if (processedEvents.contains(event.id())) {
                return;
            }

            Campaign campaign = campaigns.get(event.campaignId());

            if (campaign == null) {
                throw new NotFoundException("Campaign not found.");
            }

            if (!customers.containsKey(event.customerId())) {
                throw new NotFoundException("Customer not found.");
            }

            if (statuses.get(event.campaignId()) != CampaignStatus.ACTIVE) {
                throw new ValidationException(
                    "Events cannot be recorded for inactive campaigns."
                );
            }

            // Apply the event to a copy first. Invalid events cannot
            // partially modify the campaign ledger.
            CampaignLedger current = ledgers.get(event.campaignId());
            CampaignLedger updated = new CampaignLedger(current);

            updated.apply(event);

            ledgers.put(event.campaignId(), updated);
            processedEvents.add(event.id());

            if (event.type() == EventType.CLICK ||
                event.type() == EventType.CONVERSION) {
                journeys.computeIfAbsent(
                    event.customerId(),
                    ignored -> new ArrayList<>()
                ).add(new Touchpoint(
                    event.campaignId(),
                    event.timestamp()
                ));
            }
        }

        public void recordSpend(String campaignId, double amount) {
            Campaign campaign = campaigns.get(campaignId);

            if (campaign == null) {
                throw new NotFoundException("Campaign not found.");
            }

            CampaignLedger current = ledgers.get(campaignId);
            CampaignLedger updated = new CampaignLedger(current);

            updated.addSpend(amount, campaign.budget());

            ledgers.put(campaignId, updated);
        }

        @Override
        public CampaignReport generate(String campaignId) {
            CampaignLedger ledger = ledgers.get(campaignId);

            if (ledger == null) {
                throw new NotFoundException("Campaign not found.");
            }

            return ledger.report(campaignId);
        }

        public Map<String, Double> attribute(
            String customerId,
            AttributionModel model
        ) {
            Customer customer = customers.get(customerId);

            if (customer == null) {
                throw new NotFoundException("Customer not found.");
            }

            List<Touchpoint> events = new ArrayList<>(
                journeys.getOrDefault(customerId, List.of())
            );

            events.sort(Comparator.comparing(Touchpoint::timestamp));

            if (events.isEmpty()) {
                return Map.of();
            }

            Map<String, Double> result = new TreeMap<>();

            switch (model) {
                case FIRST_TOUCH -> result.put(
                    events.get(0).campaignId(),
                    customer.lifetimeRevenue()
                );

                case LAST_TOUCH -> result.put(
                    events.get(events.size() - 1).campaignId(),
                    customer.lifetimeRevenue()
                );

                case LINEAR -> {
                    double share =
                        customer.lifetimeRevenue() / events.size();

                    for (Touchpoint event : events) {
                        result.merge(
                            event.campaignId(),
                            share,
                            Double::sum
                        );
                    }
                }
            }

            return Map.copyOf(result);
        }

        public Map<Channel, CampaignReport> channelReport() {
            Map<Channel, List<CampaignReport>> grouped =
                new EnumMap<>(Channel.class);

            for (String id : campaigns.keySet()) {
                Campaign campaign = campaigns.get(id);

                grouped.computeIfAbsent(
                    campaign.channel(),
                    ignored -> new ArrayList<>()
                ).add(generate(id));
            }

            Map<Channel, CampaignReport> result =
                new EnumMap<>(Channel.class);

            grouped.forEach((channel, reports) -> {
                long impressions = 0;
                long clicks = 0;
                long conversions = 0;
                double spend = 0;
                double revenue = 0;

                for (CampaignReport report : reports) {
                    impressions += report.impressions();
                    clicks += report.clicks();
                    conversions += report.conversions();
                    spend += report.spend();
                    revenue += report.revenue();
                }

                result.put(
                    channel,
                    new CampaignReport(
                        channel.name(),
                        impressions,
                        clicks,
                        conversions,
                        spend,
                        revenue,
                        percent(clicks, impressions),
                        percent(conversions, clicks),
                        divide(spend, clicks),
                        divide(spend, conversions),
                        divide(revenue, spend),
                        percent(revenue - spend, spend)
                    )
                );
            });

            return Map.copyOf(result);
        }

        public Map<String, Double> customerMetrics() {
            if (customers.isEmpty()) {
                return Map.of(
                    "customerCount", 0.0,
                    "cac", 0.0,
                    "averageLtv", 0.0,
                    "ltvToCac", 0.0
                );
            }

            double acquisition = customers.values().stream()
                .mapToDouble(Customer::acquisitionCost)
                .sum();

            double lifetimeRevenue = customers.values().stream()
                .mapToDouble(Customer::lifetimeRevenue)
                .sum();

            double cac = acquisition / customers.size();
            double ltv = lifetimeRevenue / customers.size();

            return Map.of(
                "customerCount", (double) customers.size(),
                "cac", cac,
                "averageLtv", ltv,
                "ltvToCac", divide(ltv, cac)
            );
        }

        public List<CampaignReport> rankedReports() {
            return campaigns.keySet().stream()
                .map(this::generate)
                .sorted(
                    Comparator.comparingDouble(CampaignReport::roas)
                        .reversed()
                )
                .collect(Collectors.toUnmodifiableList());
        }

        public Map<String, CampaignStatus> campaignStatuses() {
            return Map.copyOf(statuses);
        }
    }

    static double divide(double a, double b) {
        return b == 0 ? 0 : a / b;
    }

    static double percent(double a, double b) {
        return divide(a, b) * 100;
    }

    static void runTests(MarketingService service) {
        CampaignReport report = service.generate("C001");

        if (Math.abs(report.ctr() - 8.0) > 0.001) {
            throw new IllegalStateException("CTR test failed.");
        }

        if (Math.abs(report.roas() - 6.0) > 0.001) {
            throw new IllegalStateException("ROAS test failed.");
        }

        Map<String, Double> attribution = service.attribute(
            "U001",
            AttributionModel.FIRST_TOUCH
        );

        if (!attribution.containsKey("C002")) {
            throw new IllegalStateException("Attribution test failed.");
        }

        System.out.println("All tests passed.");
    }

    public static void main(String[] args) {
        try {
            MarketingService service = new MarketingService();

            service.registerCampaign(new Campaign(
                "C001",
                "Search Acquisition",
                Channel.SEARCH,
                50000,
                "Customer Acquisition"
            ));

            service.registerCampaign(new Campaign(
                "C002",
                "Social Awareness",
                Channel.SOCIAL,
                40000,
                "Brand Awareness"
            ));

            service.registerCampaign(new Campaign(
                "C003",
                "Email Retention",
                Channel.EMAIL,
                20000,
                "Customer Retention"
            ));

            service.registerCustomer(new Customer(
                "U001", 500, 3000
            ));

            service.registerCustomer(new Customer(
                "U002", 400, 2500
            ));

            for (String id : List.of("C001", "C002", "C003")) {
                service.changeStatus(id, CampaignStatus.ACTIVE);
            }

            Instant time = Instant.parse("2026-02-01T10:00:00Z");

            service.recordEvent(new MarketingEvent(
                "E001", "U001", "C002",
                EventType.IMPRESSION, time, 0
            ));

            service.recordEvent(new MarketingEvent(
                "E002", "U001", "C002",
                EventType.CLICK, time.plusSeconds(60), 0
            ));

            service.recordEvent(new MarketingEvent(
                "E003", "U001", "C001",
                EventType.IMPRESSION, time.plusSeconds(120), 0
            ));

            service.recordEvent(new MarketingEvent(
                "E004", "U001", "C001",
                EventType.CLICK, time.plusSeconds(180), 0
            ));

            service.recordEvent(new MarketingEvent(
                "E005", "U001", "C001",
                EventType.CONVERSION, time.plusSeconds(240), 3000
            ));

            service.recordSpend("C001", 1000);
            service.recordSpend("C002", 500);

            runTests(service);

            System.out.println("\nCAMPAIGN REPORTS");

            service.rankedReports().forEach(System.out::println);

            System.out.println("\nCHANNEL REPORT");
            service.channelReport().forEach(
                (channel, report) ->
                    System.out.println(channel + " -> " + report)
            );

            System.out.println("\nCUSTOMER METRICS");
            System.out.println(service.customerMetrics());

            System.out.println("\nLINEAR ATTRIBUTION");
            System.out.println(service.attribute(
                "U001",
                AttributionModel.LINEAR
            ));

            System.out.println("\nCAMPAIGN STATES");
            System.out.println(service.campaignStatuses());

        } catch (MarketingException exception) {
            System.err.println(
                "Marketing operation failed: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
