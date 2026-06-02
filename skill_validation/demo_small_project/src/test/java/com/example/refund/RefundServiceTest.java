package com.example.refund;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.math.BigDecimal;
import org.junit.jupiter.api.Test;

class RefundServiceTest {
    private final RefundService refundService = new RefundService();

    @Test
    void shouldRejectZeroAmount() {
        RefundDecision decision = refundService.evaluate(
                new RefundRequest(new BigDecimal("0.00")),
                new BigDecimal("100.00"));

        assertEquals("ZERO_AMOUNT", decision.getReason());
    }
}
