<template>
  <div class="container">
    <el-row type="flex" justify="center" align="middle">
      <el-col :span="12">
        <el-form>
          <el-form-item label="公司名称">
            <el-input
              v-model="form.company_name"
              placeholder="请输入公司名称"
              clearable
              size="medium"
              :show-word-limit="true"
            />
          </el-form-item>
          <el-form-item label="社会信用代码">
            <el-input
              v-model="form.credit_number"
              placeholder="请输入统一社会信用代码"
              clearable
              size="medium"
              :show-word-limit="true"
            />
          </el-form-item>
          <el-form-item label="法定代表人">
            <el-input
              v-model="form.legal_representative"
              placeholder="请输入法定代表人"
              clearable
              size="medium"
              :show-word-limit="true"
            />
          </el-form-item>
          <el-form-item label="证券代码">
            <el-input
              v-model="form.security_code"
              placeholder="请输入证券代码"
              clearable
              size="medium"
              :show-word-limit="true"
            />
          </el-form-item>
          <el-form-item label="股票简称">
            <el-input
              v-model="form.stock_abbreviation"
              placeholder="请输入股票简称"
              clearable
              size="medium"
              :show-word-limit="true"
            />
          </el-form-item>
        </el-form>
      </el-col>
      <el-col :span="12">
        <el-button
          type="primary"
          :disabled="!isButtonEnabled"
          @click="submitQuery"
          size="medium"
          style="margin-left: 20px;"
        >
          查询
        </el-button>
      </el-col>
    </el-row>

    <el-table
      v-if="companyResults.length > 0"
      :data="companyResults"
      style="width: 100%; margin-top: 30px;"
      stripe
    >
      <el-table-column prop="company_name" label="公司中文名称" width="250px"></el-table-column>
      <el-table-column prop="credit_number" label="社会信用代码" width="250px"></el-table-column>
      <el-table-column label="操作" width="150px">
        <template v-slot:default="scope">
          <el-button @click="viewDetails(scope.row)" type="text" size="small">查看详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model='dialogVisible'
      title="公司详情"
      @close="closeDialog"
    >
      <el-form label-width="120px">
        <el-form-item label="公司中文名称">
          <el-input v-model="companyDetails.company_name" disabled></el-input>
        </el-form-item>
        <el-form-item label="社会信用代码">
          <el-input v-model="companyDetails.credit_number" disabled></el-input>
        </el-form-item>
        <el-form-item label="英文名称">
          <el-input v-model="companyDetails.english_name" disabled></el-input>
        </el-form-item>
        <el-form-item label="法定代表人">
          <el-input v-model="companyDetails.legal_representative" disabled></el-input>
        </el-form-item>
        <el-form-item label="证券代码">
          <el-input v-model="companyDetails.security_code" disabled></el-input>
        </el-form-item>
        <el-form-item label="股票简称">
          <el-input v-model="companyDetails.stock_abbreviation" disabled></el-input>
        </el-form-item>
      </el-form>

      <!-- 高级 Cypher 查询部分 -->
      <el-divider content-position="left">高级 Cypher 查询</el-divider>
      <div style="margin-bottom: 15px;">
        <el-row :gutter="10">
          <el-col :span="6">
            <el-button type="primary" size="small" @click="querySubgraph" :loading="loadingStates.subgraph">
              N跳子图查询
            </el-button>
          </el-col>
          <el-col :span="6">
            <el-button type="warning" size="small" @click="queryRiskPath" :loading="loadingStates.riskPath">
              风险分析
            </el-button>
          </el-col>
          <el-col :span="6">
            <el-button type="success" size="small" @click="queryRelationDistribution" :loading="loadingStates.relationDist">
              关系类型分布
            </el-button>
          </el-col>
          <el-col :span="6">
            <el-button type="info" size="small" @click="queryRelatedCompanyNetwork" :loading="loadingStates.relatedNetwork">
              关联公司网络
            </el-button>
          </el-col>
        </el-row>
      </div>

      <!-- N跳子图查询结果 -->
      <div v-if="subgraphResult.node_count > 0">
        <h4 style="margin-bottom: 10px;">N跳子图结果 ({{ subgraphResult.hops }}跳)</h4>
        <el-tag>节点数: {{ subgraphResult.node_count }}</el-tag>
        <el-tag type="success" style="margin-left: 10px;">边数: {{ subgraphResult.edge_count }}</el-tag>
        <el-table :data="subgraphResult.nodes" stripe size="small" max-height="200" style="margin-top: 10px;">
          <el-table-column prop="name" label="节点名称"></el-table-column>
          <el-table-column prop="type" label="节点类型"></el-table-column>
        </el-table>
      </div>

      <!-- 风险分析结果 -->
      <div v-if="riskPathResult.violation_paths?.length > 0 || riskPathResult.litigation_paths?.length > 0">
        <h4 style="margin-bottom: 10px;">风险分析</h4>
        <div v-if="riskPathResult.violation_paths?.length > 0">
          <el-tag type="danger">违规记录</el-tag>
          <el-table :data="riskPathResult.violation_paths" stripe size="small" max-height="150" style="margin-top: 5px;">
            <el-table-column prop="violation_type" label="违规类型"></el-table-column>
            <el-table-column prop="handler" label="处理单位"></el-table-column>
            <el-table-column prop="penalty_date" label="处罚日期"></el-table-column>
            <el-table-column prop="path_length" label="路径长度"></el-table-column>
          </el-table>
        </div>
        <div v-if="riskPathResult.litigation_paths?.length > 0" style="margin-top: 10px;">
          <el-tag type="warning">诉讼记录</el-tag>
          <el-table :data="riskPathResult.litigation_paths" stripe size="small" max-height="150" style="margin-top: 5px;">
            <el-table-column prop="case_reason" label="涉案缘由"></el-table-column>
            <el-table-column prop="amount" label="涉案金额"></el-table-column>
            <el-table-column prop="litigation_type" label="司法类型"></el-table-column>
            <el-table-column prop="path_length" label="路径长度"></el-table-column>
          </el-table>
        </div>
      </div>

      <!-- 关系类型分布结果 -->
      <div v-if="relationDistResult.total_outgoing > 0 || relationDistResult.total_incoming > 0">
        <h4 style="margin-bottom: 10px;">关系类型分布</h4>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-tag>出边关系 (共{{ relationDistResult.total_outgoing }}条)</el-tag>
            <el-table :data="relationDistResult.outgoing_relations" stripe size="small" max-height="150" style="margin-top: 5px;">
              <el-table-column prop="type" label="关系类型"></el-table-column>
              <el-table-column prop="count" label="数量"></el-table-column>
            </el-table>
          </el-col>
          <el-col :span="12">
            <el-tag type="success">入边关系 (共{{ relationDistResult.total_incoming }}条)</el-tag>
            <el-table :data="relationDistResult.incoming_relations" stripe size="small" max-height="150" style="margin-top: 5px;">
              <el-table-column prop="type" label="关系类型"></el-table-column>
              <el-table-column prop="count" label="数量"></el-table-column>
            </el-table>
          </el-col>
        </el-row>
      </div>

      <!-- 关联公司网络结果 -->
      <div v-if="relatedNetworkResult.company_name">
        <h4 style="margin-bottom: 10px;">关联公司网络</h4>
        <el-row :gutter="20">
          <el-col :span="8" v-if="relatedNetworkResult.subsidiaries?.length > 0">
            <el-tag type="primary">子公司 ({{ relatedNetworkResult.sub_count }})</el-tag>
            <ul style="margin: 5px 0; padding-left: 20px; font-size: 12px;">
              <li v-for="s in relatedNetworkResult.subsidiaries" :key="s">{{ s }}</li>
            </ul>
          </el-col>
          <el-col :span="8" v-if="relatedNetworkResult.customers?.length > 0">
            <el-tag type="success">客户 ({{ relatedNetworkResult.cust_count }})</el-tag>
            <ul style="margin: 5px 0; padding-left: 20px; font-size: 12px;">
              <li v-for="c in relatedNetworkResult.customers" :key="c">{{ c }}</li>
            </ul>
          </el-col>
          <el-col :span="8" v-if="relatedNetworkResult.suppliers?.length > 0">
            <el-tag type="warning">供应商 ({{ relatedNetworkResult.supplier_count }})</el-tag>
            <ul style="margin: 5px 0; padding-left: 20px; font-size: 12px;">
              <li v-for="s in relatedNetworkResult.suppliers" :key="s">{{ s }}</li>
            </ul>
          </el-col>
        </el-row>
        <div v-if="relatedNetworkResult.parents?.length > 0" style="margin-top: 10px;">
          <el-tag type="info">母公司</el-tag>
          <ul style="margin: 5px 0; padding-left: 20px; font-size: 12px;">
            <li v-for="p in relatedNetworkResult.parents" :key="p">{{ p }}</li>
          </ul>
        </div>
      </div>
      <span class="dialog-footer">
        <el-button @click="closeDialog">返回</el-button>
      </span>
    </el-dialog>

    <div style="margin-top: 20px; text-align: center; color: #888;">
      暂无匹配结果
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      form: {
        company_name: '',
        credit_number: '',
        legal_representative: '',
        security_code: '',
        stock_abbreviation: '',
      },
      companyResults: [],
      dialogVisible: false,  // 控制对话框的显示
      companyDetails: {},    // 存储公司详情
      currentCreditNumber: '', // 当前选中的公司社会信用代码
      loadingStates: {
        subgraph: false,
        riskPath: false,
        relationDist: false,
        relatedNetwork: false
      },
      subgraphResult: {},
      riskPathResult: {},
      relationDistResult: {},
      relatedNetworkResult: {}
    };
  },
  computed: {
    isButtonEnabled() {
      const filledCount = Object.values(this.form).filter(value => value).length;
      return filledCount > 0;
    },
  },
  methods: {
    async submitQuery() {
      const queryParams = Object.entries(this.form)
      // eslint-disable-next-line
        .filter(([key, value]) => value)
        .map(([key, value]) => ({ label: key, value }));

      try {
        const response = await axios.post('http://10.176.22.62:8001/querynode/', queryParams);
        if (response.data && Array.isArray(response.data)) {
          this.companyResults = response.data;
        } else {
          this.companyResults = [];
        }
      } catch (error) {
        console.error('请求失败:', error);
        this.$message.error('查询失败，请稍后重试');
      }
    },

    // 查看详情按钮点击事件
    async viewDetails(row) {
      try {
        const response = await axios.post('http://10.176.22.62:8001/qynodedtil/', {
          credit_number: row.credit_number,
        });

        if (response.data) {
          this.companyDetails = response.data;  // 设置公司详情
          this.currentCreditNumber = row.credit_number; // 保存当前公司信用代码
          this.clearCypherResults(); // 清空之前的查询结果
          this.dialogVisible = true;  // 打开对话框
        } else {
          this.$message.error('未能找到该公司详情');
        }
      } catch (error) {
        console.error('请求失败:', error);
        this.$message.error('查询公司详情失败，请稍后重试');
      }
    },

    // 清空 Cypher 查询结果
    clearCypherResults() {
      this.subgraphResult = {};
      this.riskPathResult = {};
      this.relationDistResult = {};
      this.relatedNetworkResult = {};
    },

    // 关闭对话框
    closeDialog() {
      this.dialogVisible = false;
      this.clearCypherResults();
    },

    // N跳子图查询
    async querySubgraph() {
      if (!this.currentCreditNumber) {
        this.$message.warning('请先选择一个公司');
        return;
      }
      this.loadingStates.subgraph = true;
      try {
        const response = await axios.post('http://10.176.22.62:8001/cypher_subgraph/', {
          credit_number: this.currentCreditNumber,
          hops: 2
        });
        if (response.data.status === 'success') {
          this.subgraphResult = response.data;
          this.$message.success(`查询成功，找到 ${response.data.node_count} 个节点`);
        } else {
          this.$message.error(response.data.message || '查询失败');
        }
      } catch (error) {
        console.error('N跳子图查询失败:', error);
        this.$message.error('N跳子图查询失败');
      } finally {
        this.loadingStates.subgraph = false;
      }
    },

    // 风险路径追溯
    async queryRiskPath() {
      if (!this.currentCreditNumber) {
        this.$message.warning('请先选择一个公司');
        return;
      }
      this.loadingStates.riskPath = true;
      try {
        const response = await axios.post('http://10.176.22.62:8001/risk_path/', {
          credit_number: this.currentCreditNumber
        });
        if (response.data.status === 'success') {
          this.riskPathResult = response.data;
          const totalPaths = (response.data.violation_paths?.length || 0) + (response.data.litigation_paths?.length || 0);
          if (totalPaths > 0) {
            this.$message.success(`找到 ${totalPaths} 条风险路径`);
          } else {
            this.$message.info('未发现风险路径');
          }
        } else {
          this.$message.error(response.data.message || '查询失败');
        }
      } catch (error) {
        console.error('风险路径查询失败:', error);
        this.$message.error('风险路径查询失败');
      } finally {
        this.loadingStates.riskPath = false;
      }
    },

    // 关系类型分布
    async queryRelationDistribution() {
      if (!this.currentCreditNumber) {
        this.$message.warning('请先选择一个公司');
        return;
      }
      this.loadingStates.relationDist = true;
      try {
        const response = await axios.post('http://10.176.22.62:8001/relation_distribution/', {
          credit_number: this.currentCreditNumber
        });
        if (response.data.status === 'success') {
          this.relationDistResult = response.data;
          const total = response.data.total_outgoing + response.data.total_incoming;
          if (total > 0) {
            this.$message.success(`共 ${total} 条关系`);
          } else {
            this.$message.info('未发现关系数据');
          }
        } else {
          this.$message.error(response.data.message || '查询失败');
        }
      } catch (error) {
        console.error('关系类型分布查询失败:', error);
        this.$message.error('关系类型分布查询失败');
      } finally {
        this.loadingStates.relationDist = false;
      }
    },

    // 关联公司网络
    async queryRelatedCompanyNetwork() {
      if (!this.currentCreditNumber) {
        this.$message.warning('请先选择一个公司');
        return;
      }
      this.loadingStates.relatedNetwork = true;
      try {
        const response = await axios.post('http://10.176.22.62:8001/related_company_network/', {
          credit_number: this.currentCreditNumber
        });
        if (response.data.status === 'success') {
          this.relatedNetworkResult = response.data;
          const total = response.data.sub_count + response.data.cust_count + response.data.supplier_count;
          if (total > 0) {
            this.$message.success(`找到 ${total} 家关联公司`);
          } else {
            this.$message.info('未发现关联公司');
          }
        } else {
          this.$message.error(response.data.message || '查询失败');
        }
      } catch (error) {
        console.error('关联公司网络查询失败:', error);
        this.$message.error('关联公司网络查询失败');
      } finally {
        this.loadingStates.relatedNetwork = false;
      }
    },
  },
};
</script>
<style scoped>
.container {
  padding: 20px;
}
</style>