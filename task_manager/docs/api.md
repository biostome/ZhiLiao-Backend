## 接口协议文档（Task Management Service）

- **服务名称**: Task Management Service
- **版本**: 0.1.0
- **基础路径**: `/api/v1`
- **服务默认端口**: `8000`
- **基地址示例**: `http://localhost:8000/api/v1`

### 约定
- **时间格式**: 采用 ISO 8601，例如 `2025-01-12T09:30:00Z`。
- **返回格式**: `application/json`。
- **鉴权**: 当前接口未实现鉴权（无需 Token）。
- **错误模型**: FastAPI 默认错误响应，包含 `detail` 字段；本文在各接口处标注可能的状态码。

---

## 数据模型

### 枚举
- **PriorityEnum**: `red` | `yellow` | `green`
- **StatusEnum**: `todo` | `in_progress` | `done`
- **RelationTypeEnum**: `precedes` | `parallel` | `mutex`

### LabelOut
```
{
  "id": "string-uuid",
  "name": "string"
}
```

### TaskCreate（请求体）
```
{
  "title": "string (1-255)",
  "description": "string|null",
  "priority": "red|yellow|green" (默认: yellow),
  "status": "todo|in_progress|done" (默认: todo),
  "channel": "string|null",
  "subcategory": "string|null",
  "assigned_to_user_id": "string|null",
  "created_by_user_id": "string|null",
  "start_at": "ISO8601|null",
  "due_at": "ISO8601|null",
  "labels": ["labelName", ...]  // 字符串数组，元素为标签名称
}
```

### TaskUpdate（请求体，均为可选）
```
{
  "title": "string|null",
  "description": "string|null",
  "priority": "red|yellow|green|null",
  "status": "todo|in_progress|done|null",
  "channel": "string|null",
  "subcategory": "string|null",
  "assigned_to_user_id": "string|null",
  "start_at": "ISO8601|null",
  "due_at": "ISO8601|null",
  "completed_at": "ISO8601|null",
  "labels": ["labelName", ...] | null
}
```

### TaskOut（响应体）
```
{
  "id": "string-uuid",
  "title": "string",
  "description": "string|null",
  "priority": "red|yellow|green",
  "status": "todo|in_progress|done",
  "channel": "string|null",
  "subcategory": "string|null",
  "assigned_to_user_id": "string|null",
  "created_by_user_id": "string|null",
  "start_at": "ISO8601|null",
  "due_at": "ISO8601|null",
  "completed_at": "ISO8601|null",
  "created_at": "ISO8601",
  "updated_at": "ISO8601|null",
  "labels": [LabelOut, ...]
}
```

### BatchCreateRequest（请求体）
```
{
  "tasks": [TaskCreate, ...]
}
```

### GraphResponse（响应体）
```
{
  "nodes": [
    { "id": "string-uuid", "title": "string", "priority": "red|yellow|green", "status": "todo|in_progress|done" }
  ],
  "edges": [
    { "src_task_id": "string-uuid", "dst_task_id": "string-uuid", "relation_type": "precedes|parallel|mutex" }
  ]
}
```

### RelationOp（请求体）
```
{
  "other_task_id": "string-uuid"
}
```

---

## 任务接口（/tasks）

### 创建任务
- **Method**: POST
- **Path**: `/api/v1/tasks`
- **请求体**: `TaskCreate`
- **响应**: 200 OK，`TaskOut`
- **错误**: 422 参数错误
- **示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Design API",
    "description": "Write API spec",
    "priority": "yellow",
    "status": "in_progress",
    "labels": ["api", "doc"]
  }'
```

### 批量创建任务
- **Method**: POST
- **Path**: `/api/v1/tasks/batch`
- **请求体**: `BatchCreateRequest`
- **响应**: 200 OK，`TaskOut[]`
- **错误**: 422 参数错误

### 查询任务列表
- **Method**: GET
- **Path**: `/api/v1/tasks`
- **Query 参数**:
  - `q`: string，标题/描述模糊搜索
  - `status`: `todo|in_progress|done`
  - `priority`: `red|yellow|green`
  - `label`: string，标签名称精确匹配
  - `channel`: string
  - `subcategory`: string
  - `assigned_to_user_id`: string
  - `created_by_user_id`: string
  - `due_before`: ISO8601
  - `due_after`: ISO8601
  - `sort_by`: `created_at|due_at|priority|status|title`（默认 `created_at`）
  - `sort_order`: `asc|desc`（默认 `desc`）
  - `limit`: int [1, 200]（默认 20）
  - `offset`: int >= 0（默认 0）
- **响应**: 200 OK，`TaskOut[]`

### 获取任务详情
- **Method**: GET
- **Path**: `/api/v1/tasks/{task_id}`
- **路径参数**: `task_id` string-uuid
- **响应**: 200 OK，`TaskOut`
- **错误**: 404 Not Found（任务不存在）

### 更新任务
- **Method**: PATCH
- **Path**: `/api/v1/tasks/{task_id}`
- **路径参数**: `task_id` string-uuid
- **请求体**: `TaskUpdate`
- **响应**: 200 OK，`TaskOut`
- **错误**: 404 Not Found；422 参数错误

### 删除任务
- **Method**: DELETE
- **Path**: `/api/v1/tasks/{task_id}`
- **路径参数**: `task_id` string-uuid
- **响应**: 204 No Content
- **错误**: 404 Not Found

### 集成：批量入库（同批量创建）
- **Method**: POST
- **Path**: `/api/v1/tasks/integrations/ingest`
- **请求体**: `BatchCreateRequest`
- **响应**: 200 OK，`TaskOut[]`

### 集成：任务依赖图
- **Method**: GET
- **Path**: `/api/v1/tasks/integrations/graph`
- **响应**: 200 OK，`GraphResponse`

---

## 关系接口（/relations）

以下接口用于维护任务间的三类关系：`precedes`（前驱/后继）、`parallel`（并行）、`mutex`（互斥）。

通用请求体：`RelationOp`，字段 `other_task_id`。

返回：成功时统一返回 `{ "ok": true }`，状态码如下所列。

### 添加前驱关系（other -> task）
- **Method**: POST
- **Path**: `/api/v1/relations/tasks/{task_id}/predecessors`
- **请求体**: `RelationOp`（`other_task_id` 为前驱任务 ID）
- **响应**: 201 Created，`{"ok": true}`
- **错误**: 404 Not Found（任一任务不存在）；409 Conflict（关系已存在）

### 移除前驱关系
- **Method**: DELETE
- **Path**: `/api/v1/relations/tasks/{task_id}/predecessors`
- **请求体**: `RelationOp`
- **响应**: 200 OK，`{"ok": true}`
- **错误**: 404 Not Found（关系不存在或任务不存在）

### 添加后继关系（task -> other）
- **Method**: POST
- **Path**: `/api/v1/relations/tasks/{task_id}/successors`
- **请求体**: `RelationOp`（`other_task_id` 为后继任务 ID）
- **响应**: 201 Created，`{"ok": true}`
- **错误**: 404 Not Found；409 Conflict

### 移除后继关系
- **Method**: DELETE
- **Path**: `/api/v1/relations/tasks/{task_id}/successors`
- **请求体**: `RelationOp`
- **响应**: 200 OK，`{"ok": true}`
- **错误**: 404 Not Found

### 标记并行关系（task ∥ other）
- **Method**: POST
- **Path**: `/api/v1/relations/tasks/{task_id}/parallel`
- **请求体**: `RelationOp`
- **响应**: 201 Created，`{"ok": true}`
- **错误**: 404 Not Found；409 Conflict

### 取消并行关系
- **Method**: DELETE
- **Path**: `/api/v1/relations/tasks/{task_id}/parallel`
- **请求体**: `RelationOp`
- **响应**: 200 OK，`{"ok": true}`
- **错误**: 404 Not Found

### 标记互斥关系（task ⟂ other）
- **Method**: POST
- **Path**: `/api/v1/relations/tasks/{task_id}/mutex`
- **请求体**: `RelationOp`
- **响应**: 201 Created，`{"ok": true}`
- **错误**: 404 Not Found；409 Conflict

### 取消互斥关系
- **Method**: DELETE
- **Path**: `/api/v1/relations/tasks/{task_id}/mutex`
- **请求体**: `RelationOp`
- **响应**: 200 OK，`{"ok": true}`
- **错误**: 404 Not Found

---

## 示例对象

### TaskCreate 示例
```
{
  "title": "Prepare Demo",
  "description": "Gather requirements and write slides",
  "priority": "yellow",
  "status": "todo",
  "channel": "product",
  "subcategory": "presentation",
  "assigned_to_user_id": "u_123",
  "created_by_user_id": "u_007",
  "start_at": "2025-01-10T08:00:00Z",
  "due_at": "2025-01-12T09:30:00Z",
  "labels": ["demo", "high-level"]
}
```

### TaskOut 示例
```
{
  "id": "2a3a6d47-2e7c-4f18-9b2d-3f9c3f6a7d81",
  "title": "Prepare Demo",
  "description": "Gather requirements and write slides",
  "priority": "yellow",
  "status": "in_progress",
  "channel": "product",
  "subcategory": "presentation",
  "assigned_to_user_id": "u_123",
  "created_by_user_id": "u_007",
  "start_at": "2025-01-10T08:00:00Z",
  "due_at": "2025-01-12T09:30:00Z",
  "completed_at": null,
  "created_at": "2025-01-09T12:00:00Z",
  "updated_at": "2025-01-10T09:00:00Z",
  "labels": [
    {"id": "l1", "name": "demo"},
    {"id": "l2", "name": "high-level"}
  ]
}
```

---

## 兼容性与注意事项
- 创建与批量创建接口当前返回 200（而非 201），与实现保持一致。
- 删除任务返回 204 无响应体。
- 关系新增在重复创建时返回 409 冲突。
- `due_before` / `due_after` 按字符串传入，推荐使用 ISO8601；内部进行 `<=` / `>=` 过滤。
- 列表查询中的 `label` 为标签名称精确匹配；如需复合条件可多次请求或扩展接口。

---

## 调试入口
- 本服务使用 FastAPI，开发模式可直接访问交互式文档：
  - Swagger UI: `http://localhost:8000/docs`
  - ReDoc: `http://localhost:8000/redoc`