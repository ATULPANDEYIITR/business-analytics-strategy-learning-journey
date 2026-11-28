import java.time.Duration;
import java.time.Instant;
import java.time.YearMonth;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Customer Journey Analytics
 *
 * Enterprise-oriented implementation covering:
 * - Domain modeling
 * - Event validation
 * - Consent management
 * - Identity resolution
 * - Journey state transitions
 * - Session analytics
 * - Funnel measurement
 * - Multi-touch attribution
 * - Behavioral segmentation
 * - Cohort retention
 * - Revenue reporting
 *
 * Java 17, no external dependencies.
 */
public class CustomerJourneyAnalytics {

    // ========================================================
    // 1. DOMAIN ENUMERATIONS
    // ========================================================

    enum EventType {
        AD_IMPRESSION,
        AD_CLICK,
        PAGE_VIEW,
        PRODUCT_VIEW,
        SEARCH,
        ADD_TO_CART,
        CHECKOUT,
        PURCHASE,
        SIGNUP,
        SUPPORT_REQUEST
    }

    enum Channel {
        ORGANIC_SEARCH,
        PAID_SEARCH,
        SOCIAL,
        EMAIL,
        DIRECT,
        REFERRAL,
        DISPLAY
    }

    enum ConsentStatus {
        GRANTED,
        DENIED,
        UNKNOWN
    }

    enum JourneyStage {
        AWARENESS,
        CONSIDERATION,
        CONVERSION,
        RETENTION
    }

    enum AttributionModel {
        FIRST_TOUCH,
        LAST_TOUCH,
        LINEAR,
        POSITION_BASED
    }

    enum CustomerSegment {
        VISITOR,
        ENGAGED_VISITOR,
        CART_ABANDONER,
        CONVERTED_CUSTOMER,
        REPEAT_CUSTOMER,
        SUPPORT_ENGAGED
    }

    // ========================================================
    // 2. DOMAIN EXCEPTIONS
    // ========================================================

    static class AnalyticsException extends RuntimeException {
        AnalyticsException(String message) {
            super(message);
        }
    }

    static class ValidationException extends AnalyticsException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class ConsentException extends AnalyticsException {
        ConsentException(String message) {
            super(message);
        }
    }

    static class IdentityConflictException extends AnalyticsException {
        IdentityConflictException(String message) {
            super(message);
        }
    }

    // ========================================================
    // 3. IMMUTABLE DOMAIN RECORDS
    // ========================================================

    record Customer(
        String customerId,
        ConsentStatus consent,
        Instant registeredAt
    ) {
        Customer {
            if (customerId == null || customerId.isBlank()) {
                throw new ValidationException("Customer ID is required.");
            }

            Objects.requireNonNull(consent);
            Objects.requireNonNull(registeredAt);
        }
    }

    record Touchpoint(
        String eventId,
        String customerId,
        String sessionId,
        EventType type,
        Channel channel,
        Instant timestamp,
        String page,
        String campaign,
        double value
    ) {
        Touchpoint {
            if (eventId == null || eventId.isBlank()) {
                throw new ValidationException("Event ID is required.");
            }

            if (customerId == null || customerId.isBlank()) {
                throw new ValidationException("Customer ID is required.");
            }

            if (sessionId == null || sessionId.isBlank()) {
                throw new ValidationException("Session ID is required.");
            }

            Objects.requireNonNull(type);
            Objects.requireNonNull(channel);
            Objects.requireNonNull(timestamp);

            if (page == null || page.isBlank() || page.length() > 500) {
                throw new ValidationException("Invalid page identifier.");
            }

            if (!Double.isFinite(value) || value < 0) {
                throw new ValidationException("Invalid monetary value.");
            }

            if (type == EventType.PURCHASE && value <= 0) {
                throw new ValidationException(
                    "Purchase must have positive revenue."
                );
            }
        }
    }

    record JourneyTransition(
        String customerId,
        JourneyStage previousStage,
        JourneyStage currentStage,
        EventType triggeringEvent,
        Instant timestamp
    ) {}

    record FunnelMetric(
        EventType stage,
        long customers,
        double conversionRate,
        double dropOffRate
    ) {}

    record SessionMetric(
        String customerId,
        String sessionId,
        Instant start,
        Instant end,
        long eventCount,
        Channel entryChannel,
        String exitPage
    ) {
        long durationSeconds() {
            return Duration.between(start, end).getSeconds();
        }
    }

    record CohortMetric(
        YearMonth cohortMonth,
        YearMonth activityMonth,
        long cohortSize,
        long activeCustomers,
        double retentionRate
    ) {}

    record CustomerProfile(
        int eventCount,
        int purchases,
        int cartEvents,
        int supportRequests,
        double revenue,
        CustomerSegment segment
    ) {}

    // ========================================================
    // 4. EVENT VALIDATION SERVICE
    // ========================================================

    static class EventValidationService {

        void validate(Touchpoint event) {
            Objects.requireNonNull(event, "Event cannot be null.");

            if (event.timestamp().isAfter(Instant.now().plusSeconds(300))) {
                throw new ValidationException(
                    "Event timestamp is too far in the future."
                );
            }
        }
    }

    // ========================================================
    // 5. IDENTITY RESOLUTION SERVICE
    // ========================================================

    static class IdentityService {

        private final Map<String, String> identityOwners = new HashMap<>();

        public synchronized void associate(
            String externalIdentifier,
            String customerId
        ) {
            if (externalIdentifier == null ||
                externalIdentifier.isBlank() ||
                customerId == null ||
                customerId.isBlank()) {
                throw new ValidationException(
                    "Identity identifiers cannot be empty."
                );
            }

            String existing = identityOwners.get(externalIdentifier);

            if (existing != null && !existing.equals(customerId)) {
                throw new IdentityConflictException(
                    "External identifier already belongs to another customer."
                );
            }

            identityOwners.put(externalIdentifier, customerId);
        }

        public synchronized String resolve(String identifier) {
            return identityOwners.get(identifier);
        }

        public synchronized void eraseCustomer(String customerId) {
            identityOwners.entrySet().removeIf(
                entry -> entry.getValue().equals(customerId)
            );
        }
    }

    // ========================================================
    // 6. EVENT REPOSITORY
    // ========================================================

    static class JourneyRepository {

        private final Map<String, Customer> customers = new HashMap<>();

        private final Map<String, Touchpoint> events =
            new LinkedHashMap<>();

        private final Map<String, List<String>> customerEventIds =
            new HashMap<>();

        private final EventValidationService validator =
            new EventValidationService();

        public synchronized void registerCustomer(Customer customer) {
            customers.put(customer.customerId(), customer);
        }

        public synchronized boolean record(Touchpoint event) {
            validator.validate(event);

            if (events.containsKey(event.eventId())) {
                return false;
            }

            Customer customer = customers.get(event.customerId());

            if (customer == null) {
                throw new AnalyticsException("Unknown customer.");
            }

            if (customer.consent() != ConsentStatus.GRANTED) {
                throw new ConsentException(
                    "Analytics consent is not granted."
                );
            }

            events.put(event.eventId(), event);

            customerEventIds.computeIfAbsent(
                event.customerId(),
                ignored -> new ArrayList<>()
            ).add(event.eventId());

            return true;
        }

        public synchronized List<Touchpoint> allEvents() {
            return events.values()
                .stream()
                .sorted(Comparator.comparing(Touchpoint::timestamp))
                .toList();
        }

        public synchronized List<Touchpoint> customerEvents(
            String customerId
        ) {
            return customerEventIds.getOrDefault(
                customerId,
                List.of()
            ).stream()
                .map(events::get)
                .filter(Objects::nonNull)
                .sorted(Comparator.comparing(Touchpoint::timestamp))
                .toList();
        }

        public synchronized List<Customer> customers() {
            return List.copyOf(customers.values());
        }

        public synchronized void eraseCustomer(String customerId) {
            List<String> ids = customerEventIds.remove(customerId);

            if (ids != null) {
                ids.forEach(events::remove);
            }

            customers.remove(customerId);
        }
    }

    // ========================================================
    // 7. JOURNEY STATE SERVICE
    // ========================================================

    static class JourneyStateService {

        private final Map<String, JourneyStage> currentStates =
            new HashMap<>();

        private final Map<String, List<JourneyTransition>> history =
            new HashMap<>();

        private JourneyStage classify(EventType event) {
            return switch (event) {
                case AD_IMPRESSION, AD_CLICK, PAGE_VIEW ->
                    JourneyStage.AWARENESS;

                case SEARCH, PRODUCT_VIEW, ADD_TO_CART ->
                    JourneyStage.CONSIDERATION;

                case CHECKOUT, PURCHASE ->
                    JourneyStage.CONVERSION;

                case SIGNUP, SUPPORT_REQUEST ->
                    JourneyStage.RETENTION;
            };
        }

        public synchronized JourneyTransition process(
            Touchpoint event
        ) {
            JourneyStage previous = currentStates.getOrDefault(
                event.customerId(),
                JourneyStage.AWARENESS
            );

            JourneyStage current = classify(event.type());

            JourneyTransition transition = new JourneyTransition(
                event.customerId(),
                previous,
                current,
                event.type(),
                event.timestamp()
            );

            currentStates.put(event.customerId(), current);

            history.computeIfAbsent(
                event.customerId(),
                ignored -> new ArrayList<>()
            ).add(transition);

            return transition;
        }

        public synchronized List<JourneyTransition> history(
            String customerId
        ) {
            return List.copyOf(
                history.getOrDefault(customerId, List.of())
            );
        }
    }

    // ========================================================
    // 8. SESSION ANALYSIS SERVICE
    // ========================================================

    static class SessionAnalyticsService {

        private final Duration inactivityThreshold;

        SessionAnalyticsService(Duration inactivityThreshold) {
            if (inactivityThreshold.isZero() ||
                inactivityThreshold.isNegative()) {
                throw new ValidationException(
                    "Invalid session inactivity threshold."
                );
            }

            this.inactivityThreshold = inactivityThreshold;
        }

        List<SessionMetric> analyze(List<Touchpoint> events) {
            Map<String, List<Touchpoint>> grouped = events.stream()
                .collect(Collectors.groupingBy(
                    Touchpoint::customerId,
                    HashMap::new,
                    Collectors.toList()
                ));

            List<SessionMetric> result = new ArrayList<>();

            for (List<Touchpoint> journey : grouped.values()) {
                journey.sort(
                    Comparator.comparing(Touchpoint::timestamp)
                );

                List<Touchpoint> current = new ArrayList<>();

                for (Touchpoint event : journey) {
                    if (!current.isEmpty()) {
                        Touchpoint previous = current.get(
                            current.size() - 1
                        );

                        boolean newSession =
                            !previous.sessionId().equals(event.sessionId()) ||
                            Duration.between(
                                previous.timestamp(),
                                event.timestamp()
                            ).compareTo(inactivityThreshold) > 0;

                        if (newSession) {
                            result.add(buildMetric(current));
                            current.clear();
                        }
                    }

                    current.add(event);
                }

                if (!current.isEmpty()) {
                    result.add(buildMetric(current));
                }
            }

            return result;
        }

        private SessionMetric buildMetric(List<Touchpoint> events) {
            Touchpoint first = events.get(0);
            Touchpoint last = events.get(events.size() - 1);

            return new SessionMetric(
                first.customerId(),
                first.sessionId(),
                first.timestamp(),
                last.timestamp(),
                events.size(),
                first.channel(),
                last.page()
            );
        }
    }

    // ========================================================
    // 9. FUNNEL ANALYSIS SERVICE
    // ========================================================

    static class FunnelAnalyticsService {

        private final List<EventType> stages = List.of(
            EventType.PAGE_VIEW,
            EventType.PRODUCT_VIEW,
            EventType.ADD_TO_CART,
            EventType.CHECKOUT,
            EventType.PURCHASE
        );

        List<FunnelMetric> analyze(List<Touchpoint> events) {
            Map<String, List<Touchpoint>> journeys =
                events.stream().collect(Collectors.groupingBy(
                    Touchpoint::customerId
                ));

            long[] counts = new long[stages.size()];

            for (List<Touchpoint> journey : journeys.values()) {
                journey.sort(
                    Comparator.comparing(Touchpoint::timestamp)
                );

                int nextStage = 0;

                for (Touchpoint event : journey) {
                    if (event.type() == stages.get(nextStage)) {
                        counts[nextStage]++;

                        nextStage++;

                        if (nextStage == stages.size()) {
                            break;
                        }
                    }
                }
            }

            List<FunnelMetric> result = new ArrayList<>();

            for (int i = 0; i < stages.size(); i++) {
                double previous = i == 0
                    ? counts[i]
                    : counts[i - 1];

                double conversion = previous == 0
                    ? 0
                    : counts[i] / previous;

                double dropOff = i == 0 || previous == 0
                    ? 0
                    : 1 - conversion;

                result.add(new FunnelMetric(
                    stages.get(i),
                    counts[i],
                    conversion,
                    dropOff
                ));
            }

            return List.copyOf(result);
        }
    }

    // ========================================================
    // 10. ATTRIBUTION SERVICE
    // ========================================================

    static class AttributionService {

        Map<Channel, Double> calculate(
            List<Touchpoint> events,
            AttributionModel model
        ) {
            if (events.isEmpty()) {
                return Map.of();
            }

            List<Touchpoint> ordered = events.stream()
                .sorted(Comparator.comparing(Touchpoint::timestamp))
                .toList();

            Map<Channel, Double> credits =
                new EnumMap<>(Channel.class);

            switch (model) {
                case FIRST_TOUCH ->
                    credits.put(ordered.get(0).channel(), 1.0);

                case LAST_TOUCH ->
                    credits.put(
                        ordered.get(ordered.size() - 1).channel(),
                        1.0
                    );

                case LINEAR -> {
                    double credit = 1.0 / ordered.size();

                    for (Touchpoint event : ordered) {
                        credits.merge(
                            event.channel(),
                            credit,
                            Double::sum
                        );
                    }
                }

                case POSITION_BASED -> {
                    if (ordered.size() == 1) {
                        credits.put(ordered.get(0).channel(), 1.0);
                    } else {
                        credits.merge(
                            ordered.get(0).channel(),
                            0.4,
                            Double::sum
                        );

                        credits.merge(
                            ordered.get(ordered.size() - 1).channel(),
                            0.4,
                            Double::sum
                        );

                        int middle = ordered.size() - 2;

                        if (middle > 0) {
                            double credit = 0.2 / middle;

                            for (int i = 1; i < ordered.size() - 1; i++) {
                                credits.merge(
                                    ordered.get(i).channel(),
                                    credit,
                                    Double::sum
                                );
                            }
                        }
                    }
                }
            }

            return Map.copyOf(credits);
        }

        Map<Channel, Double> allocateRevenue(
            double revenue,
            Map<Channel, Double> credits
        ) {
            if (!Double.isFinite(revenue) || revenue < 0) {
                throw new ValidationException("Invalid revenue.");
            }

            double total = credits.values().stream()
                .mapToDouble(Double::doubleValue)
                .sum();

            if (credits.isEmpty() || Math.abs(total - 1.0) > 1e-9) {
                throw new ValidationException(
                    "Attribution credits must total one."
                );
            }

            Map<Channel, Double> allocation =
                new EnumMap<>(Channel.class);

            credits.forEach((channel, credit) ->
                allocation.put(channel, revenue * credit)
            );

            return Map.copyOf(allocation);
        }
    }

    // ========================================================
    // 11. BEHAVIORAL SEGMENTATION SERVICE
    // ========================================================

    static class SegmentationService {

        private static class MutableProfile {
            int eventCount;
            int purchases;
            int cartEvents;
            int supportRequests;
            double revenue;
        }

        Map<String, CustomerProfile> analyze(
            List<Touchpoint> events
        ) {
            Map<String, MutableProfile> profiles = new HashMap<>();

            for (Touchpoint event : events) {
                MutableProfile profile = profiles.computeIfAbsent(
                    event.customerId(),
                    ignored -> new MutableProfile()
                );

                profile.eventCount++;

                switch (event.type()) {
                    case PURCHASE -> {
                        profile.purchases++;
                        profile.revenue += event.value();
                    }

                    case ADD_TO_CART -> profile.cartEvents++;

                    case SUPPORT_REQUEST -> profile.supportRequests++;

                    default -> {
                    }
                }
            }

            Map<String, CustomerProfile> result = new HashMap<>();

            profiles.forEach((customerId, profile) -> {
                CustomerSegment segment;

                if (profile.supportRequests > 0) {
                    segment = CustomerSegment.SUPPORT_ENGAGED;
                } else if (profile.purchases > 1) {
                    segment = CustomerSegment.REPEAT_CUSTOMER;
                } else if (profile.purchases == 1) {
                    segment = CustomerSegment.CONVERTED_CUSTOMER;
                } else if (profile.cartEvents > 0) {
                    segment = CustomerSegment.CART_ABANDONER;
                } else if (profile.eventCount > 3) {
                    segment = CustomerSegment.ENGAGED_VISITOR;
                } else {
                    segment = CustomerSegment.VISITOR;
                }

                result.put(customerId, new CustomerProfile(
                    profile.eventCount,
                    profile.purchases,
                    profile.cartEvents,
                    profile.supportRequests,
                    profile.revenue,
                    segment
                ));
            });

            return Map.copyOf(result);
        }
    }

    // ========================================================
    // 12. COHORT ANALYSIS SERVICE
    // ========================================================

    static class CohortAnalyticsService {

        List<CohortMetric> analyze(
            List<Customer> customers,
            List<Touchpoint> events
        ) {
            Map<String, Customer> customerMap = customers.stream()
                .collect(Collectors.toMap(
                    Customer::customerId,
                    customer -> customer
                ));

            Map<YearMonth, Set<String>> cohorts = new HashMap<>();

            for (Customer customer : customers) {
                YearMonth month = YearMonth.from(
                    customer.registeredAt().atZone(
                        java.time.ZoneOffset.UTC
                    )
                );

                cohorts.computeIfAbsent(
                    month,
                    ignored -> new HashSet<>()
                ).add(customer.customerId());
            }

            Map<YearMonth, Set<String>> monthlyActivity = new HashMap<>();

            for (Touchpoint event : events) {
                if (!customerMap.containsKey(event.customerId())) {
                    continue;
                }

                YearMonth month = YearMonth.from(
                    event.timestamp().atZone(
                        java.time.ZoneOffset.UTC
                    )
                );

                monthlyActivity.computeIfAbsent(
                    month,
                    ignored -> new HashSet<>()
                ).add(event.customerId());
            }

            List<CohortMetric> result = new ArrayList<>();

            for (var cohort : cohorts.entrySet()) {
                YearMonth cohortMonth = cohort.getKey();

                for (var activity : monthlyActivity.entrySet()) {
                    YearMonth activityMonth = activity.getKey();

                    if (activityMonth.isBefore(cohortMonth)) {
                        continue;
                    }

                    Set<String> intersection = new HashSet<>(
                        cohort.getValue()
                    );

                    intersection.retainAll(activity.getValue());

                    if (intersection.isEmpty()) {
                        continue;
                    }

                    long size = cohort.getValue().size();
                    long active = intersection.size();

                    result.add(new CohortMetric(
                        cohortMonth,
                        activityMonth,
                        size,
                        active,
                        (double) active / size
                    ));
                }
            }

            result.sort(
                Comparator.comparing(CohortMetric::cohortMonth)
                    .thenComparing(CohortMetric::activityMonth)
            );

            return List.copyOf(result);
        }
    }

    // ========================================================
    // 13. ENTERPRISE REPORTING SERVICE
    // ========================================================

    static class ReportingService {

        private final JourneyRepository repository;

        ReportingService(JourneyRepository repository) {
            this.repository = repository;
        }

        void printReport() {
            List<Touchpoint> events = repository.allEvents();

            long purchases = events.stream()
                .filter(e -> e.type() == EventType.PURCHASE)
                .count();

            double revenue = events.stream()
                .filter(e -> e.type() == EventType.PURCHASE)
                .mapToDouble(Touchpoint::value)
                .sum();

            long uniqueCustomers = events.stream()
                .map(Touchpoint::customerId)
                .distinct()
                .count();

            SessionAnalyticsService sessions =
                new SessionAnalyticsService(Duration.ofMinutes(30));

            FunnelAnalyticsService funnel =
                new FunnelAnalyticsService();

            AttributionService attribution =
                new AttributionService();

            SegmentationService segmentation =
                new SegmentationService();

            System.out.println("\nCUSTOMER JOURNEY ANALYTICS");
            System.out.println("==========================");

            System.out.println("Events: " + events.size());
            System.out.println("Customers: " + uniqueCustomers);
            System.out.println("Purchases: " + purchases);
            System.out.printf("Revenue: INR %.2f%n", revenue);

            System.out.println("\nSESSION ANALYSIS");

            for (SessionMetric session : sessions.analyze(events)) {
                System.out.printf(
                    "%s | %s | events=%d | duration=%d seconds%n",
                    session.customerId(),
                    session.sessionId(),
                    session.eventCount(),
                    session.durationSeconds()
                );
            }

            System.out.println("\nFUNNEL ANALYSIS");

            for (FunnelMetric metric : funnel.analyze(events)) {
                System.out.printf(
                    "%s | customers=%d | conversion=%.2f%% | drop-off=%.2f%%%n",
                    metric.stage(),
                    metric.customers(),
                    metric.conversionRate() * 100,
                    metric.dropOffRate() * 100
                );
            }

            System.out.println("\nCUSTOMER SEGMENTS");

            segmentation.analyze(events).forEach(
                (customerId, profile) ->
                    System.out.printf(
                        "%s -> %s, revenue=%.2f%n",
                        customerId,
                        profile.segment(),
                        profile.revenue()
                    )
            );

            System.out.println("\nC001 LINEAR ATTRIBUTION");

            Map<Channel, Double> credits = attribution.calculate(
                repository.customerEvents("C001"),
                AttributionModel.LINEAR
            );

            Map<Channel, Double> allocation =
                attribution.allocateRevenue(1499, credits);

            allocation.forEach((channel, value) ->
                System.out.printf(
                    "%s -> INR %.2f%n",
                    channel,
                    value
                )
            );
        }
    }

    // ========================================================
    // 14. DEMONSTRATION DATA
    // ========================================================

    static void populate(JourneyRepository repository) {
        Instant base = Instant.parse("2026-10-01T09:00:00Z");

        repository.registerCustomer(
            new Customer("C001", ConsentStatus.GRANTED, base)
        );

        repository.registerCustomer(
            new Customer(
                "C002",
                ConsentStatus.GRANTED,
                base.plus(Duration.ofDays(1))
            )
        );

        repository.registerCustomer(
            new Customer(
                "C003",
                ConsentStatus.GRANTED,
                base.plus(Duration.ofDays(2))
            )
        );

        repository.registerCustomer(
            new Customer(
                "C004",
                ConsentStatus.GRANTED,
                base.plus(Duration.ofDays(3))
            )
        );

        repository.registerCustomer(
            new Customer(
                "C005",
                ConsentStatus.DENIED,
                base.plus(Duration.ofDays(4))
            )
        );

        Map<String, List<Object[]>> journeys = new LinkedHashMap<>();

        journeys.put("C001", List.of(
            new Object[]{EventType.AD_CLICK, Channel.SOCIAL, 0},
            new Object[]{EventType.PAGE_VIEW, Channel.ORGANIC_SEARCH, 2},
            new Object[]{EventType.PRODUCT_VIEW, Channel.ORGANIC_SEARCH, 5},
            new Object[]{EventType.ADD_TO_CART, Channel.ORGANIC_SEARCH, 10},
            new Object[]{EventType.CHECKOUT, Channel.ORGANIC_SEARCH, 15},
            new Object[]{EventType.PURCHASE, Channel.ORGANIC_SEARCH, 20}
        ));

        journeys.put("C002", List.of(
            new Object[]{EventType.AD_CLICK, Channel.PAID_SEARCH, 0},
            new Object[]{EventType.PAGE_VIEW, Channel.PAID_SEARCH, 3},
            new Object[]{EventType.PRODUCT_VIEW, Channel.PAID_SEARCH, 7},
            new Object[]{EventType.ADD_TO_CART, Channel.PAID_SEARCH, 12}
        ));

        journeys.put("C003", List.of(
            new Object[]{EventType.PAGE_VIEW, Channel.DIRECT, 0},
            new Object[]{EventType.PRODUCT_VIEW, Channel.DIRECT, 4},
            new Object[]{EventType.CHECKOUT, Channel.DIRECT, 8},
            new Object[]{EventType.PURCHASE, Channel.DIRECT, 12}
        ));

        journeys.put("C004", List.of(
            new Object[]{EventType.AD_IMPRESSION, Channel.DISPLAY, 0},
            new Object[]{EventType.PAGE_VIEW, Channel.EMAIL, 3},
            new Object[]{EventType.PRODUCT_VIEW, Channel.EMAIL, 7}
        ));

        for (var entry : journeys.entrySet()) {
            String customerId = entry.getKey();

            int day = Integer.parseInt(customerId.substring(3));

            for (Object[] item : entry.getValue()) {
                EventType type = (EventType) item[0];
                Channel channel = (Channel) item[1];
                int minute = (int) item[2];

                Instant timestamp = base
                    .plus(Duration.ofDays(day))
                    .plus(Duration.ofMinutes(minute));

                Touchpoint event = new Touchpoint(
                    UUID.randomUUID().toString(),
                    customerId,
                    "SESSION-" + customerId,
                    type,
                    channel,
                    timestamp,
                    "/" + type.name().toLowerCase(),
                    "AUTUMN-2026",
                    type == EventType.PURCHASE ? 1499.0 : 0.0
                );

                repository.record(event);
            }
        }
    }

    // ========================================================
    // 15. AUTOMATED TESTS
    // ========================================================

    static void runTests(JourneyRepository repository) {
        List<Touchpoint> events = repository.allEvents();

        if (events.size() != 17) {
            throw new AssertionError("Incorrect event count.");
        }

        if (repository.customerEvents("C001").size() != 6) {
            throw new AssertionError("Incorrect customer event count.");
        }

        AttributionService attribution = new AttributionService();

        Map<Channel, Double> weights = attribution.calculate(
            repository.customerEvents("C001"),
            AttributionModel.LINEAR
        );

        double total = weights.values().stream()
            .mapToDouble(Double::doubleValue)
            .sum();

        if (Math.abs(total - 1) > 1e-9) {
            throw new AssertionError("Attribution weights are invalid.");
        }

        FunnelAnalyticsService funnel = new FunnelAnalyticsService();

        if (funnel.analyze(events).isEmpty()) {
            throw new AssertionError("Funnel is empty.");
        }

        boolean consentRejected = false;

        try {
            repository.record(new Touchpoint(
                "INVALID-CONSENT",
                "C005",
                "SESSION-C005",
                EventType.PAGE_VIEW,
                Channel.DIRECT,
                Instant.now(),
                "/home",
                null,
                0
            ));
        } catch (ConsentException exception) {
            consentRejected = true;
        }

        if (!consentRejected) {
            throw new AssertionError("Consent enforcement failed.");
        }

        System.out.println("\nAll enterprise validation tests passed.");
    }

    // ========================================================
    // 16. MAIN
    // ========================================================

    public static void main(String[] args) {
        try {
            JourneyRepository repository = new JourneyRepository();

            populate(repository);

            IdentityService identity = new IdentityService();

            identity.associate("web-device-001", "C001");
            identity.associate("web-device-002", "C002");

            System.out.println(
                "Resolved identity: " +
                identity.resolve("web-device-001")
            );

            JourneyStateService stateService =
                new JourneyStateService();

            for (Touchpoint event : repository.allEvents()) {
                stateService.process(event);
            }

            System.out.println(
                "C001 transitions: " +
                stateService.history("C001").size()
            );

            ReportingService reporting =
                new ReportingService(repository);

            reporting.printReport();

            CohortAnalyticsService cohortService =
                new CohortAnalyticsService();

            System.out.println("\nCOHORT RETENTION");

            for (CohortMetric metric : cohortService.analyze(
                repository.customers().stream()
                    .filter(c -> c.consent() == ConsentStatus.GRANTED)
                    .toList(),
                repository.allEvents()
            )) {
                System.out.printf(
                    "%s | %s | active=%d/%d | retention=%.2f%%%n",
                    metric.cohortMonth(),
                    metric.activityMonth(),
                    metric.activeCustomers(),
                    metric.cohortSize(),
                    metric.retentionRate() * 100
                );
            }

            runTests(repository);

        } catch (AnalyticsException exception) {
            System.err.println(
                "Analytics operation failed: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
