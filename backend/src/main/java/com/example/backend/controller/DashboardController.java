package com.example.backend.controller;

import com.example.backend.entity.WorkOrder;
import com.example.backend.repository.WorkOrderRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/dashboard")
@CrossOrigin(origins = "*")
public class DashboardController {

    @Autowired
    private WorkOrderRepository workOrderRepository;

    @GetMapping("/stats")
    public Map<String, Object> getStats() {
        List<WorkOrder> list = workOrderRepository.findAll();

        Map<String, Object> res = new HashMap<>();

        // 1. 总数
        long total = list.size();
        res.put("total", total);

        // 2. 待派单数量
        long pending = list.stream().filter(o -> "待派单".equals(o.getStatus())).count();
        res.put("pending", pending);

        // 3. 平均置信度 (如果没有数据默认 0.95)
        double avgConf = list.stream()
                .filter(o -> o.getConfidence() != null)
                .mapToDouble(WorkOrder::getConfidence)
                .average().orElse(0.95);
        res.put("avgConfidence", Math.round(avgConf * 100));

        // 4. 平均满意度 (默认 5.0)
        double avgSat = list.stream()
                .filter(o -> o.getSatisfaction() != null && o.getSatisfaction() > 0)
                .mapToInt(WorkOrder::getSatisfaction)
                .average().orElse(5.0);
        res.put("avgSatisfaction", Math.round(avgSat * 20)); // 转换为百分制

        // 5. 部门分布统计 (按主办单位分组)
        Map<String, Long> deptStats = list.stream()
                .filter(o -> o.getMainDept() != null)
                .collect(Collectors.groupingBy(WorkOrder::getMainDept, Collectors.counting()));
        res.put("deptStats", deptStats);

        return res;
    }
}