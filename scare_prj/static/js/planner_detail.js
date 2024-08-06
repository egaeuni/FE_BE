$(document).ready(function () {
  moment.locale("ko");

  // Timepicker 초기화
  $("#timepicker")
    .bootstrapMaterialDatePicker({
      date: false,
      shortTime: true,
      lang: "ko",
      cancelText: "취소",
      format: "HH:mm",
      nowButton: true,
    })
    .on("change", function (e, date) {
      var timeString = moment(date).format("HH:mm");
      var hours = timeString.split(":")[0];
      var minutes = timeString.split(":")[1];

      // 입력 필드 업데이트
      $("#time_hour").val(hours);
      $("#time_minute").val(minutes);

      // AM/PM 결정
      var amPm = hours < 12 ? "AM" : "PM";
      hours = hours % 12 || 12;
      $("#am_pm").val(amPm);

      // Timepicker 입력 필드 값 설정
      $("#am_pm_input").val(amPm);
      $("#time_hour_input").val(hours);
      $("#time_minute_input").val(minutes);
    });

  // 시간 입력 필드 클릭 시 timepicker 표시
  $("#am_pm_input, #time_hour_input, #time_minute_input").click(function () {
    $("#timepicker").focus(); // JavaScript로 timepicker에 포커스 맞추기
  });
});

document.addEventListener("DOMContentLoaded", function () {
  // 삭제 버튼 클릭 시 이벤트 처리
  document.getElementById("delete-button").addEventListener("click", function () {
    const deleteUrl = "{% url 'cal:delete_schedule' context.schedule.id %}";
    window.location.href = deleteUrl;
  });
});
