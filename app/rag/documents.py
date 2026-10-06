"""Knowledge base document definitions for Restaurant Support & Operations Agent."""

KB_DOCUMENTS = [
    {
        "doc_id": "POL-CANCEL-01",
        "title": "Order Cancellation Policy",
        "category": "Cancellation & Refunds",
        "keywords": ["cancel", "cancellation", "order cancel", "stop order", "abort"],
        "content": (
            "Order Cancellation Policy:\n"
            "1. Before Restaurant Acceptance: Customers may cancel their order free of charge with an immediate "
            "100% refund to the original payment method if the order is still in 'Placed' status and has not yet "
            "been accepted by the kitchen.\n"
            "2. After Restaurant Accepts or Starts Preparing: Once the restaurant accepts the order and kitchen "
            "preparation begins ('Confirmed' or 'Preparing' status), orders CANNOT be cancelled for a full refund "
            "because perishable ingredients and kitchen labor are already committed. In exceptional cases, a partial credit "
            "(up to 50%) may be reviewed by customer support.\n"
            "3. Out for Delivery or Delivered: Orders that are 'Out for Delivery' or 'Delivered' cannot be cancelled "
            "under any circumstances."
        )
    },
    {
        "doc_id": "POL-REFUND-02",
        "title": "Refund Policy & Payment Deduction Issues",
        "category": "Cancellation & Refunds",
        "keywords": ["refund", "deducted", "payment failed", "charged", "double charge", "money taken"],
        "content": (
            "Refund and Payment Failure Policy:\n"
            "1. Payment Deducted but Order Failed: If funds were deducted from your bank or card but the order failed "
            "to generate an order confirmation ID, the banking gateway automatically voids the pre-authorization within "
            "24 hours. If it does not reverse automatically, customer support immediately escalates a high-priority "
            "ticket to the Finance team. Refunds typically reflect in 3 to 5 business days.\n"
            "2. Missing or Damaged Items: If an order arrives with missing items or damaged packaging, customers must "
            "report it within 2 hours. A full refund for the affected item or an instant replacement credit code will be issued.\n"
            "3. Incorrect Food Delivered: If the wrong dish is delivered, the customer receives an immediate 100% refund "
            "or an express re-delivery at zero cost."
        )
    },
    {
        "doc_id": "POL-DELIVERY-03",
        "title": "Delivery Areas, Fees & ETA Guarantees",
        "category": "Delivery Operations",
        "keywords": ["delivery time", "eta", "delivery fee", "delivery area", "late delivery", "radius", "how long"],
        "content": (
            "Delivery Operations & Guidelines:\n"
            "1. Standard Delivery ETA: Delivery usually takes between 30 to 45 minutes from order confirmation, "
            "depending on dish preparation time, kitchen queue, and local traffic.\n"
            "2. Delivery Zone: We deliver within an 8-mile radius of our central restaurant hub.\n"
            "3. Delivery Charges: Flat delivery fee is $3.99. Delivery is FREE on orders totaling $35.00 or higher "
            "before taxes.\n"
            "4. Late Delivery Guarantee: If an order arrives more than 25 minutes past the quoted estimated delivery time "
            "(due to non-weather reasons), the customer is eligible for a $10 courtesy credit towards their next order."
        )
    },
    {
        "doc_id": "POL-HOURS-04",
        "title": "Operating Hours & Location",
        "category": "General Policy",
        "keywords": ["operating hours", "open time", "closing time", "location", "address", "dine-in hours"],
        "content": (
            "Operating Hours & Restaurant Information:\n"
            "- Monday to Thursday: 10:30 AM to 10:00 PM\n"
            "- Friday & Saturday: 10:30 AM to 11:30 PM\n"
            "- Sunday: 11:00 AM to 9:30 PM\n"
            "- Main Kitchen Address: 742 Gourmet Boulevard, Metropolis.\n"
            "- Dine-in reservations must be made at least 2 hours in advance via the mobile app or web portal.\n"
            "- Contact Telephone: +1-800-555-DINE (3463)."
        )
    },
    {
        "doc_id": "POL-DIET-05",
        "title": "Dietary Restrictions, Allergens & Customizations",
        "category": "Food & Safety",
        "keywords": ["allergy", "allergen", "gluten", "vegan", "vegetarian", "nuts", "halal", "dairy free"],
        "content": (
            "Allergen & Dietary Information:\n"
            "1. Menu Badges: Menu items clearly indicate Vegan (VG), Vegetarian (V), and Gluten-Free (GF) options.\n"
            "2. Allergen Notice: Our kitchen handles peanuts, tree nuts, dairy, wheat, soy, eggs, and shellfish. "
            "While strict sanitation protocols are maintained, cross-contact may occur. Customers with severe allergies "
            "must specify allergy details in the order notes and contact kitchen management directly.\n"
            "3. Customizations: Kitchen staff can accommodate basic ingredient omissions (e.g., 'no onions', 'mild spicy') "
            "when specified in item instructions during order placement."
        )
    },
    {
        "doc_id": "POL-TIPS-06",
        "title": "Tipping & Payment Methods",
        "category": "Payment Operations",
        "keywords": ["payment methods", "credit card", "apple pay", "tip", "driver tip", "cash"],
        "content": (
            "Payment & Driver Tipping:\n"
            "1. Accepted Payment Methods: Visa, MasterCard, American Express, Apple Pay, Google Pay, and PayPal.\n"
            "2. Courier Tipping: 100% of all driver tips added during checkout or upon delivery go directly to the driver.\n"
            "3. Cash Payments: Cash on delivery is available for orders under $50 in select delivery areas."
        )
    }
]

