export function columns_data_to_table_data(columns: any[], data: any[]) {
  return data.map(item => {
    const row: any = {};
    columns.forEach((column, index) => {
      row[column] = item[index];
    });
    return row;
  });
}

export function getOrderColumn(orderKey?: string) {
  switch (orderKey) {
    case 'HomeAddress':
      return '地址';
    case 'IsTenant':
      return '是否租户';
    case 'HasCoupon':
      return '是否参加问券';
    case 'VisitCount':
      return '进出次数';
    default:
      return wordMap[orderKey || ''] || '';
  }
}

export const wordMap: Record<string, string> = {
  Year: '年',
  YearMonth: '年月',
  Month: '月',
  Fee: '金额',
  CPH: '车牌号',
  TypeClass: '类型',
  VisitCount: '进出次数',
  CPHCount: '车辆数',
  DayInCount: '白天进入次数',
  DayCount: '白天出入次数',
  DayOutCount: '白天离开次数',
  NightInCount: '夜间进入次数',
  NightCount: '夜间出入次数',
  NightOutCount: '夜间离开次数',
  MaxStayHour: '最长停放小时',
  MaxStayDay: '最长停放天数',
  UserName: '名称',
  HomeAddress: '地址',
  Province: '地区',
  Count: '数量',
  CarType: '车辆类型',
  StayText: '停车时长',
  InTime: '进入时间',
  OutTime: '离开时间',
  InCount: '进入次数',
  OutCount: '离开次数',
  InGateName: '进入位置',
  OutGateName: '离开位置',
  IsTenant: '是否租户',
  CouponCPH: '问券车牌号',
  HasCoupon: '是否参加问券'
};

// 日期快捷选项
export const dateShortcuts = [
  {
    text: '最近一周',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
      return [start, end];
    }
  },
  {
    text: '最近一个月',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
      return [start, end];
    }
  },
  {
    text: '最近三个月',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
      return [start, end];
    }
  },
  {
    text: '最近一年',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 365);
      return [start, end];
    }
  },
  {
    text: '最近两年',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 365 * 2);
      return [start, end];
    }
  },
  {
    text: '最近三年',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 365 * 3);
      return [start, end];
    }
  }
];
