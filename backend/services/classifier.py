class QueryClassifier:
    @staticmethod
    def classify(query: str) -> str:
        if not query:
            return "general"
            
        q = query.lower()
        
        # Rule-based matching
        billing_keywords = ["refund", "billing", "invoice", "price", "charge", "payment", "cost", "money", "subscription"]
        coding_keywords = ["python", "code", "function", "recursion", "class", "bug", "algorithm", "javascript", "program", "compile"]
        support_keywords = ["help", "support", "ticket", "agent", "hello", "hi", "assistant", "representative"]
        technical_keywords = ["dns", "server", "ip", "database", "latency", "port", "error", "api", "connection", "network"]
        
        for word in billing_keywords:
            if word in q:
                return "billing"
                
        for word in coding_keywords:
            if word in q:
                return "coding"
                
        for word in support_keywords:
            if word in q:
                return "customer_support"
                
        for word in technical_keywords:
            if word in q:
                return "technical"
                
        return "general"
