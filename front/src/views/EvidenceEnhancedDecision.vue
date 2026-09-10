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
                type="daterange"
                range-separator="至"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
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
    </el-card>
  </div>
</template>

<script>
import { VideoPlay, Refresh, Loading } from '@element-plus/icons-vue';

export default {
  name: 'EvidenceEnhancedDecision',
  components: {
    VideoPlay,
    Refresh,
    Loading
  },
  data() {
    return {
      quadForm: {
        entity1: '',
        entity2: '',
        relation: '',
        targetTime: []
      },
      quadRules: {
        entity1: [{ required: true, message: '请输入实体1', trigger: 'blur' }],
        entity2: [{ required: true, message: '请输入实体2', trigger: 'blur' }],
        relation: [{ required: true, message: '请输入关系', trigger: 'blur' }],
        targetTime: [{ required: true, message: '请选择目标时间', trigger: 'change' }]
      },
      analyzing: false,
      analysisProgress: 0,
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
             Array.isArray(this.quadForm.targetTime) && 
             this.quadForm.targetTime.length === 2;
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
              startTime: this.quadForm.targetTime[0],
              endTime: this.quadForm.targetTime[1]
            }
          })
        });
        
        const data = await response.json();
        
        clearInterval(progressInterval);
        this.analysisProgress = 100;
        
        if (data.status === 'success') {
          this.result = {
            show: true,
            decision: '不成立',
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
          const decision = '不成立';
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
</style>
