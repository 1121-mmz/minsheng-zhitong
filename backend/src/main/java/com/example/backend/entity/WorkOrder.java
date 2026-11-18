package com.example.backend.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "work_orders")
public class WorkOrder {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String summary;
    private String mainDept;
    private String assistDept;
    private String basis;
    private Double confidence;
    private String status;
    private LocalDateTime createTime;
    private String submitter;
    private Integer satisfaction;
}