package com.example.backend.config;

import org.springframework.stereotype.Component;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;

/**
 * 无状态 Token：token = base64(username) + "." + HMAC-SHA256 签名。
 * 不再依赖内存 Map，后端重启后 token 依然有效。
 */
@Component
public class TokenStore {

    // 签名密钥（演示用，正式环境应放到配置或环境变量）
    private static final String SECRET = "minsheng-zhitong-demo-secret-key";
    private static final String HMAC_ALGO = "HmacSHA256";

    public String createToken(String username) {
        String payload = Base64.getUrlEncoder().withoutPadding()
                .encodeToString(username.getBytes(StandardCharsets.UTF_8));
        return payload + "." + sign(username);
    }

    public String getUsername(String token) {
        if (token == null) {
            return null;
        }
        try {
            String[] parts = token.split("\\.", 2);
            if (parts.length != 2) {
                return null;
            }
            String username = new String(
                    Base64.getUrlDecoder().decode(parts[0]), StandardCharsets.UTF_8);
            byte[] expected = sign(username).getBytes(StandardCharsets.UTF_8);
            byte[] actual = parts[1].getBytes(StandardCharsets.UTF_8);
            // 常量时间比较，防止时序攻击
            if (MessageDigest.isEqual(expected, actual)) {
                return username;
            }
        } catch (Exception ignored) {
            // 非法 token 一律视为无效
        }
        return null;
    }

    public void removeToken(String token) {
        // 无状态 token 无需撤销；如需主动登出失效，可引入服务端黑名单
    }

    private String sign(String username) {
        try {
            Mac mac = Mac.getInstance(HMAC_ALGO);
            mac.init(new SecretKeySpec(SECRET.getBytes(StandardCharsets.UTF_8), HMAC_ALGO));
            byte[] sig = mac.doFinal(username.getBytes(StandardCharsets.UTF_8));
            return Base64.getUrlEncoder().withoutPadding().encodeToString(sig);
        } catch (Exception e) {
            throw new RuntimeException("token 签名失败", e);
        }
    }
}
