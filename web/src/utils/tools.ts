export function columns_data_to_table_data(columns: any[], data: any[]) {
  return data.map(item => {
    const row: any = {};
    columns.forEach((column, index) => {
      row[column] = item[index];
    });
    return row;
  });
}
