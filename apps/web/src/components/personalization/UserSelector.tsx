import React from "react";

interface UserSelectorProps {
  currentUserId: string;
  onSelectUser: (userId: string) => void;
  sessionId: string;
  disabled?: boolean;
}

export const UserSelector: React.FC<UserSelectorProps> = ({
  currentUserId,
  onSelectUser,
  sessionId,
  disabled = false,
}) => {
  const users = [
    {
      id: "demo-user-a",
      displayName: "User A",
      tagline: "Prefers Energetic & High-Contrast Visuals",
      avatarBg: "linear-gradient(135deg, #f59e0b, #ec4899)",
      badgeColor: "#f59e0b",
    },
    {
      id: "demo-user-b",
      displayName: "User B",
      tagline: "Prefers Calm & Minimalistic Ambient Visuals",
      avatarBg: "linear-gradient(135deg, #06b6d4, #10b981)",
      badgeColor: "#10b981",
    },
  ];

  return (
    <div
      style={{
        backgroundColor: "rgba(30, 41, 59, 0.7)",
        borderRadius: "0.75rem",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        padding: "1rem 1.25rem",
        display: "flex",
        flexWrap: "wrap",
        gap: "1rem",
        justifyContent: "space-between",
        alignItems: "center",
        backdropFilter: "blur(12px)",
      }}
    >
      {/* User Switcher Buttons */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
        <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "#94a3b8" }}>
          Active User Profile:
        </span>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          {users.map((u) => {
            const isSelected = currentUserId === u.id;
            return (
              <button
                key={u.id}
                type="button"
                disabled={disabled}
                onClick={() => onSelectUser(u.id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.6rem",
                  padding: "0.45rem 0.9rem",
                  borderRadius: "0.5rem",
                  backgroundColor: isSelected
                    ? "rgba(56, 189, 248, 0.18)"
                    : "rgba(15, 23, 42, 0.6)",
                  border: `1.5px solid ${
                    isSelected ? u.badgeColor : "rgba(255, 255, 255, 0.08)"
                  }`,
                  color: isSelected ? "#f8fafc" : "#94a3b8",
                  cursor: disabled ? "not-allowed" : "pointer",
                  boxShadow: isSelected ? `0 0 14px ${u.badgeColor}33` : "none",
                  transition: "all 0.2s ease",
                }}
              >
                <div
                  style={{
                    width: "22px",
                    height: "22px",
                    borderRadius: "50%",
                    background: u.avatarBg,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "0.7rem",
                    fontWeight: 800,
                    color: "#ffffff",
                    boxShadow: "0 2px 4px rgba(0,0,0,0.3)",
                  }}
                >
                  {u.displayName.split(" ")[1]}
                </div>
                <div style={{ textAlign: "left" }}>
                  <div style={{ fontSize: "0.85rem", fontWeight: 700 }}>{u.displayName}</div>
                  <div style={{ fontSize: "0.68rem", opacity: 0.7 }}>{u.id}</div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Session ID Indicator */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
        <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Session Stream:</span>
        <code
          style={{
            fontSize: "0.78rem",
            backgroundColor: "rgba(15, 23, 42, 0.8)",
            padding: "0.25rem 0.6rem",
            borderRadius: "0.375rem",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            color: "#38bdf8",
            fontFamily: "monospace",
          }}
        >
          {sessionId}
        </code>
      </div>
    </div>
  );
};
