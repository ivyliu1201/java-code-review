package com.example.checkout;

import org.springframework.transaction.annotation.Transactional;

public class CheckoutService {
    private final OrderRepository orderRepository;
    private final PaymentClient paymentClient;
    private final AuditRepository auditRepository;

    public CheckoutService(
            OrderRepository orderRepository,
            PaymentClient paymentClient,
            AuditRepository auditRepository) {
        this.orderRepository = orderRepository;
        this.paymentClient = paymentClient;
        this.auditRepository = auditRepository;
    }

    @Transactional
    public void completeCheckout(CheckoutRequest request) {
        orderRepository.save(request.toOrder());
        paymentClient.charge(request.getPaymentToken(), request.getAmount());
        auditRepository.save(AuditLog.success(request.getOrderId()));
    }
}
