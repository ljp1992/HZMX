odoo.define('document_multi_upload', function (require) {
"use strict";

var core = require('web.core');
var FormView = require('web.FormView');
var framework = require('web.framework');
var _t = core._t;

FormView.include({
    render_buttons: function() {
        var self = this;
        var add_button = false;
        if(!self.$buttons){
            add_button = true;
        }
        self._super.apply(self, arguments);
        if(add_button && self.$buttons){
            self.$buttons.find('.o_form_file_upload_input').change(function(evt){
                var target = evt.target;
                var $form = $(target.form);
                var $file = $(target);
                var value = $file.val();
                console.log("form file input change value : ", value);
                if($file.val() !== ''){
                    var $badge = $form.find(".badge");
                    var serialize = $form.serializeArray();
                    var files = $file.get(0).files;
                    if(!files){
                        if(self.sidebar){
                            self.sidebar.do_attachement_update(self.dataset, self.datarecord.id, [{
                                "error": _t("Unsupported browsers and versions!")
                            }]);
                        }
                        return;
                    }
                    var count = files.length;
                    var error = [];
                    console.log("form file input serialize object : ", serialize);
                    console.log("form file input select count : ", count);
                    framework.blockUI();
                    $badge.text(count);
                    _.each(files, function(file, index){
                        var data = new FormData();
                        var last_file = false;
                        data.append('id', self.datarecord.id);
                        data.append('ufile', file);
                        if (files.length === index + 1){
                            last_file =true;
                        }
                        data.append('last_file', last_file);
                        _.each(serialize, function(param){
                            data.append(param.name, param.value);
                        });

                        // alert($form.attr("action")+data);
                        // $.ajax({
                        //     url: $form.attr("action"),
                        //     type: 'POST',
                        //     data: data,
                        //     dataType: 'json',
                        //     cache: false,
                        //     processData: false,
                        //     contentType: false,
                        //     success: function(ret){
                        //         alert('success');
                        //         console.log("form file(%s) upload result : ", index, ret);
                        //         if(ret.error){
                        //             error.push([ret.error,ret.message].join(":"));
                        //         }
                        //         count--;
                        //         if(count == 0){
                        //             framework.unblockUI();
                        //             if(self.sidebar){
                        //                 self.sidebar.do_attachement_update(self.dataset, self.datarecord.id, [{
                        //                     "error": error.join("<br/>")
                        //                 }]);
                        //             }
                        //         }
                        //         $badge.text(count ? count : "");
                        //     }
                        // });

                        //原先的ajax不知道为啥 有时无法将信息发送到服务器
                        $.ajax({
                            type: 'POST',
                            url: $form.attr("action"),
                            dataType: 'json',
                            data: data,
                            cache: false,
                            processData: false,
                            contentType: false,
                            async: false,
                            success: function (data) {
                                if (data.error){
                                    alert(data.error);
                                    return self.$buttons;
                                }
                            },
                        });
                        window.location.reload();
                    });
                    $file.val("");
                }
            });
        }
        return self.$buttons;
    }
});

});