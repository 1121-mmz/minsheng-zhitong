package com.example.backend.controller;

import com.example.backend.entity.WorkOrder;
import com.example.backend.repository.WorkOrderRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class TriageController {

    // 注入数据库操作接口
    @Autowired
    private WorkOrderRepository workOrderRepository;

    private final RestTemplate restTemplate = new RestTemplate();

    // 1. 智能分诊接口 (转发给 Python)
    @PostMapping("/triage")
    public Map<String, Object> triage(@RequestBody Map<String, Object> request) {
        String text = String.valueOf(request.get("text"));
        // 直接转发整个请求体（text + history），多轮澄清需要历史
        Map<String, Object> pythonRequest = new HashMap<>(request);

        String pythonUrl = System.getenv("AI_SERVICE_URL") != null ? System.getenv("AI_SERVICE_URL") : "http://localhost:8000/triage";

        try {
            return restTemplate.postForObject(pythonUrl, pythonRequest, Map.class);
        } catch (Exception e) {
            Map<String, Object> error = new HashMap<>();
            error.put("summary", text);
            error.put("mainDept", "系统异常");
            error.put("assistDept", "AI服务未连接");
            error.put("basis", "请检查 8000 端口是否启动");
            error.put("confidence", 0);
            return error;
        }
    }

    // 2. 保存工单接口 (前端点“确认派发”时调用)
    @PostMapping("/orders")
    public WorkOrder createOrder(@RequestBody WorkOrder order) {
        System.out.println("========== 收到保存工单请求 ==========");
        order.setCreateTime(LocalDateTime.now());
        if (order.getStatus() == null || order.getStatus().isEmpty()) {
            order.setStatus("已派单");
        }
        WorkOrder savedOrder = workOrderRepository.save(order);
        System.out.println("========== 工单入库成功，ID: " + savedOrder.getId() + " ==========");
        return savedOrder;
    }

    // 3. 查询所有工单接口 (给工单流转中心用的)
    @GetMapping("/orders")
    public List<WorkOrder> getAllOrders() {
        System.out.println("========== 收到查询工单列表请求 ==========");
        return workOrderRepository.findAll();
    }

    // 4. 管理员审核并派单接口
    @PutMapping("/orders/{id}")
    public WorkOrder updateOrder(@PathVariable Long id, @RequestBody WorkOrder updatedOrder) {
        return workOrderRepository.findById(id).map(order -> {
            // 只允许修改这几个字段
            order.setMainDept(updatedOrder.getMainDept());
            order.setAssistDept(updatedOrder.getAssistDept());
            order.setBasis(updatedOrder.getBasis());
            order.setStatus("已派单"); // 审核通过后变成已派单
            return workOrderRepository.save(order);
        }).orElseThrow(() -> new RuntimeException("工单不存在"));
    }

    // 5. 市民查询自己的诉求
    @GetMapping("/orders/my/{submitter}")
    public List<WorkOrder> getMyOrders(@PathVariable String submitter) {
        // 这里简单处理：查出所有，然后过滤（实际项目中应在数据库用 SQL 查）
        return workOrderRepository.findAll().stream()
                .filter(o -> submitter.equals(o.getSubmitter()))
                .toList();
    }

    // 6. 市民评价满意度
    @PutMapping("/orders/rate/{id}/{score}")
    public WorkOrder rateOrder(@PathVariable Long id, @PathVariable Integer score) {
        return workOrderRepository.findById(id).map(order -> {
            order.setSatisfaction(score);
            return workOrderRepository.save(order);
        }).orElseThrow(() -> new RuntimeException("工单不存在"));
    }

    // 7. 管理员删除工单
    @DeleteMapping("/orders/{id}")
    public Map<String, Object> deleteOrder(@PathVariable Long id) {
        workOrderRepository.deleteById(id);
        Map<String, Object> res = new HashMap<>();
        res.put("success", true);
        res.put("message", "工单已删除");
        return res;
    }
}