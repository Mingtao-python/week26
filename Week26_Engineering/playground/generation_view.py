from decoder import greedy_decode, temperature_sample

class GenerationView:
    def __init__(self, temperature=0.7):
        self.temperature = temperature
    
    def set_temperature(self, temperature):
        """Set the temperature for generation."""
        self.temperature = temperature
    
    def generate(self, prompt, logits, temperature=None):
        """Generate a token using greedy or temperature sampling based on temperature setting."""
        vocab = ["apple", "banana", "cat", "dog", "tree"]
        
        # Use provided temperature or default
        temp = temperature if temperature is not None else self.temperature
        
        # Handle temperature=0 as greedy mode
        if temp == 0:
            token, probs = greedy_decode(logits, vocab)
            method = "greedy"
        elif temp is None or temp <= 0:
            raise ValueError("temperature must be > 0 for sampling mode")
        else:
            token, probs = temperature_sample(logits, vocab, temp)
            method = "temperature_sample"
        
        return {
            "prompt": prompt,
            "token": token,
            "probs": probs,
            "temperature": temp,
            "method": method
        }
