frappe.provide('void');

frappe.ui.form.on("Purchase Order", {
	onload: function(frm) {
	    console.log('onload');

		frm.add_custom_button(__("Void Document"), function (frm) {

			frappe.confirm(
		'Are you sure you want to cancel this Document?',
		function(){
				console.log('HELLO HI');
			  frappe.call({
				  method: "void.void.po.void_so",
				  args: {
					  "docname": cur_frm.doc.name
				  },
				  callback: function (r) {
				  	console.log(r);
					  window.location.reload();
				  }
			  });
			// window.close();
		},
		function(){
			// show_alert('Thanks for continue here!')
		}
	);


		}).addClass("btn-primary")
    }
});