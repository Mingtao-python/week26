import json
import os
from ui import PlaygroundUI
from tokenizer_view import TokenizerView
from context_view import ContextView
from generation_view import GenerationView
from failure_view import FailureView

# Import logger from parent directory
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from experiment_logger import log_experiment

class PlaygroundApp:
    def __init__(self):
        self.ui = PlaygroundUI()
        
        # Load settings from settings.json
        settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
        self.settings = self._load_settings(settings_path)
        
        # Initialize views with settings
        self.tokenizer = TokenizerView()
        self.context = ContextView()
        self.generation = GenerationView(temperature=self.settings.get("temperature", 0.7))
        self.failure = FailureView()
        
        # Current experiment state
        self.current_test_case = None
        self.current_context = None
        self.last_output = None
    
    def _load_settings(self, path):
        """Load settings from JSON file."""
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "temperature": 0.7,
            "max_output_tokens": 200,
            "context_policy": "priority_trim",
            "log_experiments": True
        }
    
    def run(self):
        while True:
            choice = self.ui.menu()

            if choice == "1":
                text = self.ui.get_text("Enter text to tokenize:")
                tokens = self.tokenizer.tokenize(text)
                self.ui.show_tokens(tokens)

            elif choice == "2":
                ctx = self.ui.get_multiline("Enter context items:")
                result = self.context.inspect(ctx)
                self.ui.show_context(result)

            elif choice == "3":
                prompt = self.ui.get_text("Enter prompt:")
                logits = self.ui.get_logits()
                # Get temperature from user or use default
                temp_input = self.ui.get_text(f"Enter temperature (default: {self.settings.get('temperature', 0.7)}):")
                try:
                    temp = float(temp_input) if temp_input.strip() else self.settings.get("temperature", 0.7)
                except ValueError:
                    temp = self.settings.get("temperature", 0.7)
                
                result = self.generation.generate(prompt, logits, temp)
                self.ui.show_generation(result)

            elif choice == "4":
                output = self.ui.get_text("Enter model output:")
                evidence = self.ui.get_text("Enter evidence:")
                answerable_input = self.ui.get_text("Is this answerable? (y/n):")
                answerable = answerable_input.lower() != 'n'
                result = self.failure.simple_classify(output, evidence, answerable)
                self.ui.show_failure(result)
            
            elif choice == "5":
                # Run Experiment Mode - integrated workflow
                self._run_experiment()

            elif choice == "0":
                print("Exiting playground.")
                break
    
    def _run_experiment(self):
        """Run a complete experiment with test case, settings, context, generation, and logging."""
        print("\n=== Run Experiment Mode ===")
        
        # Step 1: Load or create test case
        print("\n[Step 1] Load Test Case")
        test_file = self.ui.get_text("Enter test case file (or press Enter for sample):")
        
        if test_file.strip() and os.path.exists(test_file.strip()):
            with open(test_file.strip(), "r", encoding="utf-8") as f:
                tests = json.load(f)
                if tests:
                    self.current_test_case = tests[0]  # Load first test case
                    print(f"Loaded test case: {self.current_test_case.get('id', 'N/A')}")
        else:
            # Create sample test case
            question = self.ui.get_text("Enter question:")
            evidence = self.ui.get_text("Enter evidence:")
            answerable_input = self.ui.get_text("Is this answerable? (y/n):")
            self.current_test_case = {
                "id": "manual_001",
                "question": question,
                "evidence": evidence,
                "answerable": answerable_input.lower() != 'n',
                "expected_behavior": "answer" if answerable_input.lower() != 'n' else "abstain"
            }
        
        # Step 2: Set generation parameters
        print("\n[Step 2] Set Generation Parameters")
        temp_input = self.ui.get_text(f"Enter temperature (default: {self.settings.get('temperature', 0.7)}):")
        try:
            temperature = float(temp_input) if temp_input.strip() else self.settings.get("temperature", 0.7)
        except ValueError:
            temperature = self.settings.get("temperature", 0.7)
        
        self.generation.set_temperature(temperature)
        print(f"Temperature set to: {temperature}")
        
        # Step 3: Setup context with layers
        print("\n[Step 3] Setup Context")
        system_prompt = self.ui.get_text("System prompt:")
        history = self.ui.get_text("Conversation history:")
        user_input = self.current_test_case.get("question", "")
        evidence_list = [self.current_test_case.get("evidence", "")]
        
        self.current_context = {
            "system": system_prompt,
            "history": history,
            "user": user_input,
            "evidence": evidence_list
        }
        
        # Calculate token budget
        context_info = self.context.inspect(self.current_context)
        budget = self.context.calculate_budget(
            capacity=16000,
            reserved_output=self.settings.get("max_output_tokens", 200),
            safety_margin=800,
            system_tokens=context_info.get("system", {}).get("tokens", 0),
            history_tokens=context_info.get("history", {}).get("tokens", 0),
            user_tokens=context_info.get("user", {}).get("tokens", 0),
            evidence_tokens=context_info.get("evidence", {}).get("tokens", 0)
        )
        
        print("\n--- Token Budget ---")
        if budget.get("status") == "OVERFLOW":
            print(f"⚠️ OVERFLOW! Excess: {budget.get('overflow')} tokens")
            print("Recommendation: Trim old history or low-priority evidence")
        else:
            print(f"Capacity: {budget.get('capacity')}")
            print(f"Input: {budget.get('input_tokens')}")
            print(f"Reserved output: {budget.get('reserved_output')}")
            print(f"Safety: {budget.get('safety_margin')}")
            print(f"Remaining: {budget.get('remaining')}")
            print(f"Utilization: {budget.get('utilization', 0):.1f}%")
        
        # Step 4: Run generation
        print("\n[Step 4] Run Generation")
        logits_input = self.ui.get_text("Enter logits (space-separated, or press Enter for default):")
        if logits_input.strip():
            logits = [float(x) for x in logits_input.split()]
        else:
            logits = [2.0, 1.0, 0.5, 0.2, 0.1]  # Default logits
        
        gen_result = self.generation.generate(user_input, logits, temperature)
        self.last_output = gen_result["token"]
        
        print(f"\nGenerated token: {gen_result['token']}")
        print(f"Method: {gen_result['method']}")
        print(f"Temperature: {gen_result['temperature']}")
        print(f"Probabilities: {[f'{p:.3f}' for p in gen_result['probs']]}")
        
        # Step 5: Classify failure
        print("\n[Step 5] Classify Output")
        failure_label = self.failure.classify(self.last_output, self.current_test_case)
        print(f"Failure classification: {failure_label}")
        
        # Step 6: Log experiment
        print("\n[Step 6] Log Experiment")
        if self.settings.get("log_experiments", True):
            exp_id = log_experiment({
                "test_case_id": self.current_test_case.get("id", "manual"),
                "question": self.current_test_case.get("question", ""),
                "evidence": self.current_test_case.get("evidence", ""),
                "context": self.current_context,
                "settings": {
                    "temperature": temperature,
                    "max_output_tokens": self.settings.get("max_output_tokens", 200)
                },
                "output": self.last_output,
                "generation_method": gen_result["method"],
                "probabilities": gen_result["probs"],
                "token_budget": budget,
                "failure_label": failure_label
            })
            print(f"Experiment logged with ID: {exp_id}")
        else:
            print("Logging disabled in settings.")
        
        print("\n=== Experiment Complete ===")
