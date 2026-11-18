package com.example.backend.config;

public class AuthContext {

    private static final ThreadLocal<String> CURRENT_USERNAME = new ThreadLocal<>();

    private AuthContext() {
    }

    public static void setUsername(String username) {
        CURRENT_USERNAME.set(username);
    }

    public static String getUsername() {
        return CURRENT_USERNAME.get();
    }

    public static void clear() {
        CURRENT_USERNAME.remove();
    }
}
