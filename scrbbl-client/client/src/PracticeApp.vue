<template>
  <div id="app" class="app">
    <navigation @openCreator="openPracticeCreator" />
    <div class="main">
      <router-view @openCreator="openPracticeCreator" />
    </div>
    <room-creator
      :isVisible="isModalVisible"
      @closeCreator="closeCreator"
    ></room-creator>
    <foot></foot>
    </div>
</template>
<script>
import Nav from "./components/Nav.vue";
import Footer from "./components/Footer.vue";
import RoomCreator from "./components/RoomCreator.vue";
import PracticeRoomCreator from "./components/PracticeRoomCreator.vue";

export default {
  name: "PracticeApp",
  data() {
    return { users: [], isModalVisible: false, name: null };
  },
  components: {
    navigation: Nav,
    foot: Footer,
    "room-creator": RoomCreator,
    //"practice-creator": PracticeRoomCreator,
  },
  methods: {
    leaveRoom() {
      this.$socket.emit("leave_room");
    },
    openPracticeCreator() {
      this.$data.isModalVisible = true;
    },
    closeCreator() {
      this.$data.isModalVisible = false;
    },
  },
  sockets: {
    room_created(id) {
      this.$router.push({ name: "room", params: { id: id } });
    },
  },
  watch: {
    async $route(to, from) {
      if (from.name == "room") {
        this.leaveRoom();
      }
    },
  },
};
</script>
<style lang="scss">
@import "./styles/variables.scss";
.app {
  margin: 0;
  position: relative;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.subtitle {
  a {
    color: $link;
  }
}

.main {
  flex: 1;
}

.section-xs {
  @media screen and (max-width: 670px) {
    padding: 1.5rem;
  }
}
</style>
