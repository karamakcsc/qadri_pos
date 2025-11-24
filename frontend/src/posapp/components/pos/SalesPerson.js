// A function to fetch sales persons based on POS Profile.

export function get_sales_person_names() {
  const vm = this;
  if (vm.pos_profile.posa_local_storage && getSalesPersonsStorage().length) {
    try {
      vm.sales_persons = getSalesPersonsStorage();
    } catch (e) {}
  }
  frappe.call({
    method: "posawesome.posawesome.api.utilities.get_sales_person_names",
    callback: function (r) {
      if (r.message && r.message.length > 0) {
        vm.sales_persons = r.message.map((sp) => ({
          value: sp.name,
          title: sp.sales_person_name,
          sales_person_name: sp.sales_person_name,
          name: sp.name,
        }));
        if (vm.pos_profile.posa_local_storage) {
          setSalesPersonsStorage(vm.sales_persons);
        }
      } else {
        vm.sales_persons = [];
      }
    },
  });
}
