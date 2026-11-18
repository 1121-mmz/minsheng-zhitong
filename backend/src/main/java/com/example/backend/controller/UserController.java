package com.example.backend.controller;

import com.example.backend.config.AuthContext;
import com.example.backend.config.TokenStore;
import com.example.backend.entity.User;
import com.example.backend.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.web.bind.annotation.*;
import jakarta.annotation.PostConstruct;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class UserController {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private TokenStore tokenStore;

    private final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();

    // 项目启动时初始化账号，并把历史明文密码升级为 BCrypt
    @PostConstruct
    public void initUsers() {
        if (userRepository.count() == 0) {
            User superAdmin = new User();
            superAdmin.setUsername("admin");
            superAdmin.setPassword(encoder.encode("123456"));
            superAdmin.setRole("SUPER_ADMIN");
            superAdmin.setCreateTime(LocalDateTime.now());
            userRepository.save(superAdmin);

            User user = new User();
            user.setUsername("user");
            user.setPassword(encoder.encode("123456"));
            user.setRole("USER");
            user.setCreateTime(LocalDateTime.now());
            userRepository.save(user);
        } else {
            User existingAdmin = userRepository.findByUsername("admin");
            if (existingAdmin != null && !"SUPER_ADMIN".equals(existingAdmin.getRole())) {
                existingAdmin.setRole("SUPER_ADMIN");
                userRepository.save(existingAdmin);
            }
        }

        // 密码升级：把历史明文密码（或任何非 BCrypt 格式）统一转成 BCrypt
        for (User u : userRepository.findAll()) {
            String pwd = u.getPassword();
            if (pwd == null || !pwd.startsWith("$2")) {
                u.setPassword(encoder.encode(pwd == null ? "123456" : pwd));
                userRepository.save(u);
            }
        }
    }

    // 登录
    @PostMapping("/auth/login")
    public Map<String, Object> login(@RequestBody Map<String, String> request) {
        String username = request.get("username");
        String password = request.get("password");
        Map<String, Object> response = new HashMap<>();

        User user = userRepository.findByUsername(username);
        if (user != null && password != null && encoder.matches(password, user.getPassword())) {
            String token = tokenStore.createToken(username);
            System.out.println("[Auth] 登录成功，签发 token=" + token.substring(0, Math.min(30, token.length())) + "...");
            response.put("success", true);
            response.put("token", token);
            response.put("username", user.getUsername());
            response.put("role", user.getRole());
        } else {
            response.put("success", false);
            response.put("message", "账号或密码错误");
        }
        return response;
    }

    // 获取所有用户列表
    @GetMapping("/users")
    public List<User> getAllUsers() {
        return userRepository.findAll();
    }

    // 新增用户/管理员
    @PostMapping("/users")
    public User createUser(@RequestBody User user) {
        String operator = AuthContext.getUsername();
        if ("ADMIN".equals(user.getRole()) && !"admin".equals(operator)) {
            throw new RuntimeException("只有超级管理员 admin 才能新增管理员！");
        }

        user.setId(null);
        if (user.getRole() == null || user.getRole().isEmpty()) {
            user.setRole("USER");
        }
        user.setCreateTime(LocalDateTime.now());
        if (user.getPassword() == null || user.getPassword().isEmpty()) {
            user.setPassword("123456");
        }
        user.setPassword(encoder.encode(user.getPassword()));
        return userRepository.save(user);
    }

    // 删除用户
    @DeleteMapping("/users/{id}")
    public Map<String, Object> deleteUser(@PathVariable Long id) {
        String operator = AuthContext.getUsername();
        User targetUser = userRepository.findById(id).orElse(null);
        if (targetUser == null) {
            throw new RuntimeException("用户不存在");
        }

        if (("ADMIN".equals(targetUser.getRole()) || "SUPER_ADMIN".equals(targetUser.getRole()))
                && !"admin".equals(operator)) {
            throw new RuntimeException("只有超级管理员 admin 才能删除管理员！");
        }

        if ("SUPER_ADMIN".equals(targetUser.getRole())) {
            throw new RuntimeException("系统超级管理员不可被删除！");
        }

        userRepository.deleteById(id);
        Map<String, Object> res = new HashMap<>();
        res.put("success", true);
        return res;
    }
}
