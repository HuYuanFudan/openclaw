<template>
  <div class="evidence-enhanced-decision">
    <h1>证据增强决策</h1>
    <p class="description">
      输入候选四元组，系统将自动查找相关的时序路径证据，并根据证据判断该事实是否在目标时间成立
    </p>
    
    <!-- 候选四元组输入 -->
    <el-card class="input-card">
      <template #header>
        <span>候选四元组输入</span>
      </template>
      
      <el-form :model="quadForm" label-width="120px" :rules="quadRules" ref="quadFormRef">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="实体1 (E₁)" prop="entity1">
              <el-input 
                v-model="quadForm.entity1" 
                placeholder="请输入起始实体"
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="实体2 (Eₖ)" prop="entity2">
              <el-input 
                v-model="quadForm.entity2" 
                placeholder="请输入目标实体"
                clearable
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="关系 (R)" prop="relation">
              <el-input 
                v-model="quadForm.relation" 
                placeholder="请输入关系类型"
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="目标时间 (τ)" prop="targetTime">
              <el-date-picker
                v-model="quadForm.targetTime"
                type="date"
                placeholder="选择目标时间"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item>
          <el-button 
            type="primary" 
            :loading="analyzing"
            :disabled="!canAnalyze"
            @click="startAnalyze"
          >
            <el-icon><video-play /></el-icon>
            开始判定
          </el-button>
          <el-button @click="resetAll">
            <el-icon><refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 分析过程 -->
    <el-card v-if="analyzing" class="result-card">
      <div class="analyzing-container">
        <el-icon class="analyzing-icon"><loading /></el-icon>
        <p>正在分析时序路径证据...</p>
        <el-progress :percentage="analysisProgress" :status="analysisProgress === 100 ? 'success' : ''" />
      </div>
    </el-card>
    
    <!-- 判定结果 -->
    <el-card v-if="result.show" class="result-card">
      <template #header>
        <div class="result-header">
          <span>判定结果</span>
          <el-tag 
            :type="result.decision === '成立' ? 'success' : 'danger'" 
            size="large"
            effect="dark"
          >
            {{ result.decision }}
          </el-tag>
        </div>
      </template>
      
      <div class="result-content">
        <!-- 四元组信息 -->
        <div class="quadruple-section">
          <h4>待判定事实</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="实体1">{{ quadForm.entity1 }}</el-descriptions-item>
            <el-descriptions-item label="实体2">{{ quadForm.entity2 }}</el-descriptions-item>
            <el-descriptions-item label="关系">{{ quadForm.relation }}</el-descriptions-item>
            <el-descriptions-item label="目标时间">{{ quadForm.targetTime }}</el-descriptions-item>
          </el-descriptions>
        </div>
        
        <!-- 判定理由 -->
        <div class="reason-section">
          <h4>判定理由</h4>
          <el-timeline>
            <el-timeline-item
              v-for="(reason, index) in result.reasons"
              :key="index"
              :type="reason.type"
            >
              {{ reason.content }}
            </el-timeline-item>
          </el-timeline>
        </div>
        
        <!-- 查看路径按钮 -->
        <div class="view-paths-action">
          <el-button 
            type="info" 
            text
            size="small"
            @click="showPaths = !showPaths"
          >
            <el-icon><view /></el-icon>
            {{ showPaths ? '隐藏' : '查看' }}时序路径证据 ({{ result.paths.length }}条)
          </el-button>
        </div>
        
        <!-- 时序路径证据（折叠显示） -->
        <el-collapse-transition>
          <div v-show="showPaths" class="paths-section">
            <h4>时序路径证据</h4>
            <div v-for="(path, pathIndex) in result.paths" :key="pathIndex" class="path-item">
              <div class="path-header">
                <span class="path-title">路径 {{ pathIndex + 1 }}</span>
                <el-tag :type="path.valid ? 'success' : 'danger'" size="small">
                  {{ path.valid ? '有效' : '无效' }}
                </el-tag>
              </div>
              
              <div class="path-visualization">
                <div 
                  v-for="(node, nodeIndex) in path.nodes" 
                  :key="nodeIndex"
                  class="path-node-wrapper"
                >
                  <div class="entity-box" :class="{ 'highlight': nodeIndex === 0 || nodeIndex === path.nodes.length - 1 }">
                    <div class="entity-name">{{ node.entity }}</div>
                  </div>
                  
                  <template v-if="nodeIndex < path.nodes.length - 1">
                    <div class="edge-container">
                      <div class="edge-arrow">→</div>
                      <div class="edge-info">
                        <el-tag size="small" type="info">{{ node.relation }}</el-tag>
                        <div class="edge-time">{{ node.timestamp }}</div>
                      </div>
                      <div class="edge-arrow">→</div>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </el-collapse-transition>
      </div>
    </el-card>
  </div>
</template>

<script>
import { VideoPlay, Refresh, Loading, View } from '@element-plus/icons-vue';

export default {
  name: 'EvidenceEnhancedDecision',
  components: {
    VideoPlay,
    Refresh,
    Loading,
    View
  },
  data() {
    return {
      quadForm: {
        entity1: '',
        entity2: '',
        relation: '',
        targetTime: ''
      },
      quadRules: {
        entity1: [{ required: true, message: '请输入实体1', trigger: 'blur' }],
        entity2: [{ required: true, message: '请输入实体2', trigger: 'blur' }],
        relation: [{ required: true, message: '请输入关系', trigger: 'blur' }],
        targetTime: [{ required: true, message: '请选择目标时间', trigger: 'change' }]
      },
      analyzing: false,
      analysisProgress: 0,
      showPaths: false,
      result: {
        show: false,
        decision: '',
        reasons: [],
        paths: []
      }
    };
  },
  computed: {
    canAnalyze() {
      return this.quadForm.entity1 && 
             this.quadForm.entity2 && 
             this.quadForm.relation && 
             this.quadForm.targetTime;
    }
  },
  methods: {
    // 开始分析
    async startAnalyze() {
      const valid = await this.$refs.quadFormRef.validate().catch(() => false);
      if (!valid) return;
      
      this.analyzing = true;
      this.analysisProgress = 0;
      this.result.show = false;
      this.showPaths = false;
      
      // 模拟进度
      const progressInterval = setInterval(() => {
        if (this.analysisProgress < 90) {
          this.analysisProgress += Math.floor(Math.random() * 15) + 5;
          if (this.analysisProgress > 90) this.analysisProgress = 90;
        }
      }, 300);
      
      try {
        const response = await fetch('http://10.176.22.62:8001/evidence_decision/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            quadruple: {
              entity1: this.quadForm.entity1,
              entity2: this.quadForm.entity2,
              relation: this.quadForm.relation,
              targetTime: this.quadForm.targetTime
            }
          })
        });
        
        const data = await response.json();
        
        clearInterval(progressInterval);
        this.analysisProgress = 100;
        
        if (data.status === 'success') {
          this.result = {
            show: true,
            decision: data.decision || '未知',
            reasons: data.reasons || [],
            paths: data.paths || []
          };
          this.$message.success('判定完成');
        } else {
          throw new Error(data.message || '判定失败');
        }
      } catch (error) {
        console.error('判定失败:', error);
        clearInterval(progressInterval);
        this.analysisProgress = 100;
        
        // 模拟数据展示
        setTimeout(() => {
          const decision = Math.random() > 0.3 ? '成立' : '不成立';
          this.result = {
            show: true,
            decision: decision,
            reasons: [
              { type: 'primary', content: `系统分析了 3 条时序路径证据` },
              { type: decision === '成立' ? 'success' : 'danger', content: decision === '成立' ? '多数路径支持该事实在目标时间成立' : '路径证据不足以支持该事实成立' },
              { type: 'warning', content: '部分路径时间戳与目标时间存在偏差，已进行时间一致性校正' }
            ],
            paths: [
              {
                valid: true,
                nodes: [
                  { entity: this.quadForm.entity1, relation: '投资', timestamp: '2023-03-15' },
                  { entity: '中间公司A', relation: '控股', timestamp: '2023-06-20' },
                  { entity: this.quadForm.entity2 }
                ]
              },
              {
                valid: true,
                nodes: [
                  { entity: this.quadForm.entity1, relation: '合作', timestamp: '2023-01-10' },
                  { entity: this.quadForm.entity2 }
                ]
              },
              {
                valid: false,
                nodes: [
                  { entity: this.quadForm.entity1, relation: '收购', timestamp: '2022-12-01' },
                  { entity: '子公司B', relation: '合并', timestamp: '2023-05-15' },
                  { entity: '中间公司C', relation: '持股', timestamp: '2023-08-20' },
                  { entity: this.quadForm.entity2 }
                ]
              }
            ]
          };
          this.$message.success('判定完成（演示模式）');
        }, 500);
      } finally {
        setTimeout(() => {
          this.analyzing = false;
        }, 500);
      }
    },
    
    // 重置所有
    resetAll() {
      this.$refs.quadFormRef.resetFields();
      this.result.show = false;
      this.result.decision = '';
      this.result.reasons = [];
      this.result.paths = [];
      this.showPaths = false;
    }
  }
};
</script>

<style scoped>
.evidence-enhanced-decision {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

h1 {
  margin-bottom: 10px;
  color: #303133;
}

.description {
  color: #606266;
  margin-bottom: 20px;
}

.input-card,
.result-card {
  margin-bottom: 20px;
}

.analyzing-container {
  text-align: center;
  padding: 40px;
}

.analyzing-icon {
  font-size: 48px;
  color: #409eff;
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-content {
  padding: 10px;
}

.quadruple-section,
.reason-section {
  margin-bottom: 25px;
}

.quadruple-section h4,
.reason-section h4,
.paths-section h4 {
  margin-bottom: 15px;
  color: #303133;
  border-left: 4px solid #409eff;
  padding-left: 10px;
  font-size: 16px;
}

.view-paths-action {
  margin: 20px 0;
  text-align: center;
}

.paths-section {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
  margin-top: 15px;
}

.path-item {
  margin-bottom: 20px;
  background: #fff;
  padding: 15px;
  border-radius: 8px;
}

.path-item:last-child {
  margin-bottom: 0;
}

.path-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.path-title {
  font-weight: bold;
  color: #303133;
  font-size: 14px;
}

.path-visualization {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  overflow-x: auto;
}

.path-node-wrapper {
  display: flex;
  align-items: center;
}

.entity-box {
  min-width: 100px;
  padding: 10px 15px;
  background: #fff;
  border: 2px solid #dcdfe6;
  border-radius: 8px;
  text-align: center;
  transition: all 0.3s;
}

.entity-box.highlight {
  border-color: #409eff;
  background: #ecf5ff;
  box-shadow: 0 2px 12px 0 rgba(64, 158, 255, 0.2);
}

.entity-name {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.edge-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 15px;
  min-width: 120px;
}

.edge-arrow {
  color: #909399;
  font-size: 16px;
  font-weight: bold;
}

.edge-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  padding: 8px;
  background: #e4e7ed;
  border-radius: 4px;
  margin: 5px 0;
}

.edge-time {
  font-size: 12px;
  color: #606266;
}

:deep(.el-timeline-item__node) {
  background-color: transparent;
}

:deep(.el-descriptions__label) {
  width: 120px;
  justify-content: flex-end;
}
</style>
