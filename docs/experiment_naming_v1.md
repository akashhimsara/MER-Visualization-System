# Experiment Naming Convention v1

Format:

EXP_<FAMILY>_<NUMBER>

Experiment Families:

TRAD = Traditional engineered-feature baseline
MERT = MERT representation experiment
HYBRID = Hybrid representation experiment
TEMP = Temporal context/hop experiment
OPT = Optimization experiment
RT = Real-time system experiment
FINAL = Final locked evaluation

Examples:

EXP_TRAD_001
EXP_TRAD_002

EXP_MERT_001
EXP_MERT_002

EXP_HYBRID_001

EXP_TEMP_001
EXP_TEMP_002

EXP_OPT_001

EXP_RT_001

EXP_FINAL_001

Each Experiment ID must uniquely identify one experimental configuration.

Existing Experiment IDs must never be reused for a different configuration.