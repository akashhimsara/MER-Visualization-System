import matplotlib.pyplot as plt


methods = [
    "Proposed Adaptive",
    "Immediate Reactive",
    "Fixed Rule-Based"
]

transition_counts = [
    1,
    2,
    2
]


plt.bar(methods, transition_counts)

plt.xlabel("Method")
plt.ylabel("Transition Count")
plt.title("Transition Count Comparison")

plt.tight_layout()

plt.savefig(
    "results/transition_count_comparison.png",
    dpi=300
)

plt.show()