import math

if __package__ and "." in __package__:
    from ..decoder import greedy_decode, temperature_sample
else:
    from decoder import greedy_decode, temperature_sample

class GenerationView:
    def __init__(self, temperature=0.7):
        self.set_temperature(temperature)
    
    def set_temperature(self, temperature):
        """Set the temperature for generation."""
        if not math.isfinite(temperature) or temperature < 0:
            raise ValueError("temperature must be finite and >= 0")
        self.temperature = temperature
    
    def generate(self, prompt, logits, temperature=None, vocab=None):
        """Generate a token using greedy or temperature sampling based on temperature setting."""
        vocab = vocab if vocab is not None else ["apple", "banana", "cat", "dog", "tree"]
        
        # Use provided temperature or default
        temp = temperature if temperature is not None else self.temperature
        if not math.isfinite(temp) or temp < 0:
            raise ValueError("temperature must be finite and >= 0")
        
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
